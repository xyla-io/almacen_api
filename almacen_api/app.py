import flask

from .api import AlmacenAPI, api
from data_layer import Redshift as SQL
from .companies import companies_blueprints

query_schema = {
  'type': 'object',
  'properties': {
    'query': {
      'type': 'string',
      'minLength': 1,
    },
    'substitution_parameters': {
      'type': 'array',
      'items': {
        'type': 'string',
      },
    },
  },
  'requiredProperties': ['query'],
  'additionalProperties': False,
}

app = flask.Flask(api.configuration['name'])
api.configure_app(app=app)

@app.errorhandler(AlmacenAPI.Error)
def handle_almacen_error(error: AlmacenAPI.Error):
  response = flask.jsonify(error.to_dict())
  response.status_code = error.code
  return response

@app.route('/', methods=['GET'])
def home():
  return "<h1>Almacen API</h1><p>This site is a prototype API for Almacén.</p>"

@app.route('/query', methods=['POST'])
@api.check_privileges([AlmacenAPI.Privilege.super])
def query():
  body = api.valid_body_from_request(
    request=flask.request, 
    schema=query_schema
  )
  query = SQL.Query(
    query=body['query'], 
    substitution_parameters=tuple(body['substitution_parameters']) if 'substitution_parameters' in body else ()
  )
  try:
    response = api.run_query(query)
  except Exception as error:
    raise AlmacenAPI.Error(code=424, message='Error running query.', error=error)
  
  return response

for blueprint in companies_blueprints:
  app.register_blueprint(blueprint)