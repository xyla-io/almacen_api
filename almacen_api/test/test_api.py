import pytest
import json

from data_layer import Redshift as SQL
from time import sleep

headers = [('Authorization', 'Bearer TOKEN')]

@pytest.fixture
def client():
  from config import sql_config
  SQL.Layer.configure_connection(sql_config['default'])
  from ..app import app

  # def exception():
  #   raise Exception('test exception')
  # app.route('/exception', methods=['GET'])(exception)

  client = app.test_client()

  yield client

def test_query(client):
  """Test the query route."""
  
  query_response = client.post('/query', headers=headers)
  assert query_response.status_code == 400

  query_response = client.post('/query', headers=headers, content_type='application/json', data=json.dumps({'query': 'SELECT * FROM `tag_ads`', 'parameters': [1]}))
  assert query_response.status_code == 400

  query_response = client.post('/query', headers=headers, content_type='application/json', data=json.dumps({'query': 'SELECT * FROM `tag_ads`'}))
  assert query_response.status_code == 200

def test_home(client):
  """Test the home route."""

  home_response = client.get('/')
  assert b'Almacen API' in home_response.data

# def test_exception(client):
#   """Test the exception route."""
#   exception_response = client.get('/exception')
#   assert 500 == exception_response.status_code

#   home_response = client.get('/')
#   assert b'Almacen API' in home_response.data