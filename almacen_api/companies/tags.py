import flask
import json
import pandas as pd

from ..api import AlmacenAPI, api
from .tags_validation import ParseMethod, parse_schema, update_schema, update_parser_schema, parser_parse_schema, parser_update_tags_schema
from threading import Thread
from typing import Dict
from data_layer import Redshift as SQL
from io_map import IOMap, IOMapKey, IOMapValueType, IOMapGraph, IOMapEach, IOMapZip, IOMapCall, IOMapConstantKey
from io_channel import IOSequenceParser, IOSwitchParser, IORegexParser
from subir import Uploader
from moda import log
from io_almacen.tag import NameTagsProcessor, TagParserModel, SelectTagParserMapsQuery, SelectTagsQuery, RefreshTagsQuery, PutTagParserMapQuery, DeleteTagParserMapQuery, StandardTagsUpdater

url_tags_blueprint = flask.Blueprint('url_tags', __name__, url_prefix='/companies/<identifier>/tags')

@url_tags_blueprint.route('', methods=['PUT', 'PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def update_tags(identifier: str):
  body = api.valid_body_from_request(
    request=flask.request,
    schema=update_schema()
  )
  merge_replace = flask.request.method == 'PUT'
  merge_column_names = [
    'url',
    'set',
    *(['key'] if not merge_replace else []),
  ]
  data_frame = pd.DataFrame(body['tags'])

  try:
    uploader = Uploader()
    uploader.upload_data_frame(
      schema_name=identifier,
      table_name='tags',
      merge_column_names=merge_column_names,
      data_frame=data_frame,
      column_type_transform_dictionary={},
      merge_replace=merge_replace
    )
  except ValueError as e:
    raise AlmacenAPI.Error(code=400, message='Upload error.', error=e)
  except SQL.LoadError as e:
    raise AlmacenAPI.Error(code=400, message='Data format error.', error=e)
  except Exception as e:
    raise AlmacenAPI.Error(code=500, message='Unknown upload error.')    

  Thread(target=refresh_tags, kwargs={'schema': identifier}).start()

  return flask.jsonify({
    'success': True
  })

@url_tags_blueprint.route('', methods=['GET'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def get_tags(identifier: str):
  include_empty = flask.request.args.get('include_empty') == '1'
  query = SelectTagsQuery(
    schema=identifier,
    include_empty=include_empty
  )
  return api.run_query(query=query)

def refresh_tags(schema: str):
  query = RefreshTagsQuery(schema=schema)
  sql_layer = SQL.Layer()
  sql_layer.connect()
  query.run(sql_layer=sql_layer)
  notices = sql_layer.connection.notices
  sql_layer.commit()
  sql_layer.disconnect()
  newline = '\n'
  log.log(f'Refreshed tags: {newline.join(notices)}' if notices else 'Refreshed tags.')

@url_tags_blueprint.route('/parsers', methods=['GET'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def get_tag_parsers(identifier: str):
  query = SelectTagParserMapsQuery(schema=identifier)
  result = api.execute_query(query=query)
  return flask.jsonify({
    'success': True,
    'parsers': [
      {
        c: json.loads(r[i]) if c == 'key_map' else r[i]
        for i, c in enumerate(result.column_names)
      }
      for r in result.rows
    ],
  })

@url_tags_blueprint.route('parsers/<parser>', methods=['PUT'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def update_tag_parser(identifier: str, parser: str):
  body = api.valid_body_from_request(
    request=flask.request,
    schema=update_parser_schema()
  )
  put_parser_query = PutTagParserMapQuery(
    schema=identifier,
    name=parser,
    key_map=body['key_map']
  )
  return api.run_query(query=put_parser_query)

@url_tags_blueprint.route('parsers/<parser>', methods=['DELETE'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def delete_tag_parser(identifier: str, parser: str):
  delete_parser_query = DeleteTagParserMapQuery(
    schema=identifier,
    name=parser
  )
  return api.run_query(query=delete_parser_query)

@url_tags_blueprint.route('/parsers/<parser>/parse', methods=['POST'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def parser_parse_tags(identifier: str, parser: str):
  body = api.valid_body_from_request(
    request=flask.request,
    schema=parser_parse_schema()
  )
  parser_maps_query = SelectTagParserMapsQuery(schema=identifier)
  parser_maps_result = api.execute_query(query=parser_maps_query)
  parser_key_maps = {
    r[1]: json.loads(r[2])
    for r in parser_maps_result.rows
  }

  parser_url = f'{TagParserModel.maps_url_prefix}{parser}'
  if parser_url not in parser_key_maps:
    raise AlmacenAPI.Error(404, f'Parser {parser} not found')
  parser_key_map = parser_key_maps[parser_url]
  parser_provider_map = IOMapConstantKey(
    key_constant=f'join.["str.iokeymap.{TagParserModel.maps_url_prefix}", "run.0"]',
    fallback_keys=[f'json.{IOMapValueType.json.format(IOMapConstantKey(key_constant="json.{}")._construct_key_map)}'],
  )

  graph = IOMapGraph(key_maps=[
    {
      IOMapKey.map.value: IOMapEach(key_map=parser_key_map),
      IOMapKey.input.value: 'input.names',
      IOMapKey.output.value: 'run.tags',
    },
    {
      IOMapKey.map.value: IOMapZip(),
      IOMapKey.input.value: {
        'keys': 'input.names',
        'values': 'input.tags',
      },
      IOMapKey.output.value: 'output.name_tags',
    }
  ])

  with IOMap._local_registries():
    IOMap._register_map_identifiers([
      'io_map.util/IOMapConstantKey',
      'io_channel.parse/IOSequenceParser',
      'io_channel.parse/IORegexParser',
      'io_channel.parse/IOSwitchParser',
    ])
    IOMap._register_key_maps(key_maps={
      **parser_key_maps,
      'parser_provider': parser_provider_map._construct_key_map,
    })
    name_tags = graph.run(names=body['names'])['name_tags']
  return flask.jsonify({
    'success': True,
    'message': f'{len(name_tags)} names parsed.',
    'name_tags': name_tags,
  })

@url_tags_blueprint.route('/parsers/<parser>/tag', methods=['POST'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def parser_update_tags(identifier: str, parser: str):
  body = api.valid_body_from_request(
    request=flask.request,
    schema=parser_update_tags_schema()
  )
  processor = NameTagsProcessor(schema=identifier)
  tags = processor.run(
    urls_to_names=body['urls_to_names'],
    parser_url=f'{TagParserModel.maps_url_prefix}{parser}',
    update_mode=body['update_mode'] if 'update_mode' in body and body['update_mode'] != 'dry_run' else None
  )
  return flask.jsonify({
    'success': True,
    'message': f'{sum(len(v) for v in tags.values())} tags applied to {len(tags)} entities.',
    'tags': tags,
  })

@url_tags_blueprint.route('/standard', methods=['POST'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def replace_standard_tags(identifier: str):
  updater = StandardTagsUpdater(schema=identifier)
  updater.run()
  return flask.jsonify({
    'success': True
  })
