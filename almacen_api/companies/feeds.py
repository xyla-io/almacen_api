import flask
import subir
import json

from . import feeds_validation
from ..api import AlmacenAPI, api
from data_layer import Redshift as SQL
from typing import List
from psycopg2.errors import DuplicateTable, UndefinedTable, UndefinedObject

feeds_blueprint = flask.Blueprint('feeds', __name__, url_prefix='/companies/<identifier>/feeds')

@feeds_blueprint.route('utils/structure/csv', methods=['POST'])
@api.check_privileges([AlmacenAPI.Privilege.feeder])
def infer_csv_table_structure(identifier):
  file = api.get_file(key='csv_file')
  uploader = subir.Uploader()
  column_types = uploader.get_table_structure(csv_stream=file.stream)

  return flask.jsonify({
    'column_types': column_types
  })

@feeds_blueprint.route('tables/<table_name>', methods=['GET'])
@api.check_privileges([AlmacenAPI.Privilege.feeder])
def get_table(identifier, table_name):
  uploader = subir.Uploader()
  try:
    column_types = uploader.get_column_types(schema_name=identifier, table_name=table_name)
  except ValueError as e:
    raise AlmacenAPI.Error(code=400, message='Invalid table name.', error=e)
  return flask.jsonify({
    c: t.value
    for c, t in column_types.items()
  })

@feeds_blueprint.route('tables/<table_name>', methods=['PUT'])
@api.check_privileges([AlmacenAPI.Privilege.feeder])
def create_table(identifier, table_name):
  body = api.valid_body_from_request(
    request=flask.request,
    schema=feeds_validation.crate_table_schema
  )
  uploader = subir.Uploader()
  try:
    query = uploader.create_table_query(
      schema_name=identifier,
      table_name=table_name,
      column_types=body['column_types'],
      read_only_groups=body['read_only_groups'] if 'read_only_groups' in body else []
    )
    return api.run_query(query=query)
  except ValueError as e:
    raise AlmacenAPI.Error(code=400, message='Invalid table definition.', error=e)
  except DuplicateTable as e:
    raise AlmacenAPI.Error(code=409, message=f'A table named {table_name} already exists.')
  except UndefinedObject as e:
    raise AlmacenAPI.Error(code=400, message='Undefined object:', error=e)

@feeds_blueprint.route('tables/<table_name>', methods=['DELETE'])
@api.check_privileges([AlmacenAPI.Privilege.feeder])
def delete_table(identifier, table_name):
  uploader = subir.Uploader()
  try:
    query = uploader.delete_table_query(
      schema_name=identifier,
      table_name=table_name,
    )
    return api.run_query(query=query)
  except ValueError as e:
    raise AlmacenAPI.Error(code=400, message='Invalid table name.', error=e)
  except UndefinedTable as e:
    raise AlmacenAPI.Error(code=404, message=f'No table named {table_name} exists.')

def upload_table_data(identifier: str, table_name: str, merge_column_names: List[str], should_replace: bool):
  file = api.get_file(key='csv_file')

  try:
    uploader = subir.Uploader()
    uploader.upload(
      schema_name=identifier,
      table_name=table_name,
      merge_column_names=[] if should_replace else merge_column_names,
      csv_stream=file.stream,
      replace=should_replace
    )
  except ValueError as e:
    raise AlmacenAPI.Error(code=400, message='Upload error.', error=e)
  except SQL.LoadError as e:
    raise AlmacenAPI.Error(code=400, message='Data format error.', error=e)
  except Exception as e:
    raise AlmacenAPI.Error(code=500, message='Unknown upload error.')

  return flask.jsonify({
    'success': True
  })

@feeds_blueprint.route('tables/<table_name>/replace', methods=['PUT'])
@api.check_privileges([AlmacenAPI.Privilege.feeder])
def replace_table_data(identifier, table_name):
  return upload_table_data(
    identifier=identifier,
    table_name=table_name,
    merge_column_names=[],
    should_replace=True
  )

@feeds_blueprint.route('tables/<table_name>/merge', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.feeder])
def merge_table_data(identifier, table_name):
  merge_info_json = api.get_form_json(key='options')
  api.validate_json(json=merge_info_json, schema=feeds_validation.merge_table_data_schema)

  return upload_table_data(
    identifier=identifier,
    table_name=table_name,
    merge_column_names=[c.lower() for c in merge_info_json['merge_column_names']],
    should_replace=False
  )
