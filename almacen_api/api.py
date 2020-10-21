import os
import flask
import jsonschema
import re
import json
import datetime
import functools

from time import sleep
from enum import Enum
from typing import List, Dict, Tuple, Optional
from data_layer import Redshift as SQL
from config import almacen_api_config, sql_config

class AlmacenAPI:
  class Privilege(Enum):
    super = 'super'
    tagger = 'tagger'
    reader = 'reader'
    feeder = 'feeder'

  class QueryResult:
    row_count: int
    column_names: Optional[List[str]]
    rows: Optional[List[List[any]]]

    def __init__(self, row_count: int, column_names: Optional[List[str]]=None, rows: Optional[List[List[any]]]=None):
      self.row_count = row_count
      self.column_names = column_names
      self.rows = rows

  class Error(Exception):
    code: int
    message: str
    error: Exception

    def __init__(self, code: int, message: str, error: Optional[Exception]=None):
      self.code = code
      self.message = message
      self.error = error

    def to_dict(self):
      return {
        'message': '{message} {error}'.format(message=self.message, error=self.error) if self.error is not None else self.message,
      }

  configuration: Dict[str, any]

  def __init__(self, configuration: Dict[str, any]):
    self.configuration = configuration
    self.app = flask.Flask(self.configuration['name'])

  def configure_app(self, app: flask.Flask):
    if 'app' not in self.configuration:
      return
    app.config.from_mapping(self.configuration['app'])

  def check_privileges(self, privileges: List[Privilege]=[]):
    def wrap(f):
      @functools.wraps(f)
      def wrapper(*args, **kwargs):
        self.validate_privileges(privileges=privileges)
        return f(*args, **kwargs)
      return wrapper
    return wrap

  def validate_privileges(self, privileges: List[Privilege]=[]):
    authorization = flask.request.headers.get('Authorization')
    if authorization is not None:
      match = re.fullmatch(r'(B|b)earer ([^\s]+)', authorization)
      if match is not None:
        token = match.group(2)
        if token in self.configuration['app_tokens']:
          app_configuration = self.configuration['app_tokens'][token]
          app_privileges = {AlmacenAPI.Privilege(r) for r in app_configuration['roles']}
          if AlmacenAPI.Privilege.super in app_privileges or app_privileges.issuperset(privileges):
            return
          else:
            raise AlmacenAPI.Error(code=403, message='Access denied.')

    raise AlmacenAPI.Error(code=401, message='Unauthenticated.')
  
  def validate_json(self, json: any, schema: Dict[str, any]):
    try:
      jsonschema.validate(json, schema)
    except jsonschema.exceptions.ValidationError as error:
      raise AlmacenAPI.Error(code=400, message='Invalid request body.', error=error)

  def valid_body_from_request(self, request: flask.Request, schema: Dict[str, any]):
    json = request.get_json()
    self.validate_json(json=json, schema=schema)
    return json
  
  def to_json(self, any: any) -> str:
    date_handler = lambda obj: (
      obj.isoformat()
      if isinstance(obj, (datetime.datetime, datetime.date))
      else None
    )
    return json.dumps(any, default=date_handler)

  def execute_query(self, query: SQL.Query) -> QueryResult:
    sql_layer = SQL.Layer()
    sql_layer.connect()
    cursor = query.run(sql_layer=sql_layer)
    if cursor.description is not None:
      column_names = [c.name for c in cursor.description]
      rows = cursor.fetchall()
      result = AlmacenAPI.QueryResult(row_count=cursor.rowcount, column_names=column_names, rows=rows)
    else:
      result = AlmacenAPI.QueryResult(row_count=cursor.rowcount)
    sql_layer.commit()
    sql_layer.disconnect()
    return result

  def run_query(self, query: SQL.Query):
    sql_layer = SQL.Layer()
    sql_layer.connect()
    cursor = query.run(sql_layer=sql_layer)

    if cursor.description is None:
      response = flask.jsonify({
        'column_names': None,
        'rows': None,
        'row_count': cursor.rowcount,
      })
      sql_layer.commit()
      sql_layer.disconnect()
      return response

    column_names = [c.name for c in cursor.description]
    def generate():
      yield '{{"column_names": {column_names}, "rows": ['.format(column_names=self.to_json(column_names))
      prefix = ''
      while True:
        rows = cursor.fetchmany(size=1000)
        if not rows: break
        yield prefix + ', '.join([self.to_json(r) for r in rows])
        prefix = ', '
      row_count = cursor.rowcount
      sql_layer.commit()
      sql_layer.disconnect()
      yield '], "row_count": {row_count}}}'.format(row_count=self.to_json(row_count))

    return flask.Response(generate(), mimetype='application/json')

  def get_file(self, key: str) -> any:
    if key not in flask.request.files:
      raise AlmacenAPI.Error(code=400, message=f'A file with key \'{key}\' is required.')
    return flask.request.files[key]

  def get_form_json(self, key: str) -> any:
    if key not in flask.request.form:
      raise AlmacenAPI.Error(code=400, message=f'A form field with key \'{key}\' is required.')
    try:
      value = json.loads(flask.request.form[key])
      return value
    except json.JSONDecodeError as e:
      raise AlmacenAPI.Error(code=400, message=f'The \'{key}\' form field must be valid JSON.', error=e)

  @property
  def s3_configuration(self) -> Dict[str, any]:
    return self.configuration['s3_query_results_bucket']

  @property
  def debug(self) -> bool:
    return self.configuration['debug'] if 'debug' in self.configuration else False


configuration_name = os.environ['ALMACEN_API_CONFIGURATION']
configuration = almacen_api_config[configuration_name]

SQL.Layer.configure_connection(sql_config[configuration['database']])
api = AlmacenAPI(configuration=configuration)