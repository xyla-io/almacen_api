import flask
import itertools

from . import tag_validation
from .entities import Entity, entities_blueprint
from ..api import AlmacenAPI, api
from datetime import datetime
from data_layer import Redshift as SQL
from typing import List, Dict, Optional
from subir import Tagger

time_format = '%Y-%m-%d %H:%M:%S'
tags_blueprint = flask.Blueprint('tags', __name__, url_prefix='/companies/<identifier>/entities/<entity_type>/tags')

# DEPRECATED
# TODO remove this when longcat_ux is updated
def tag_entities_query(company_identifier: str, entity: Entity, entity_array: List[Dict[str, any]], tag: str, subtag: Optional[str]=None) -> SQL.Query:
  upload_group = 'almacen_api {date}'.format(date=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
  rows = [[company_identifier, c['app'], c['channel'], str(c[entity.id_column_name]), tag, subtag, upload_group] for c in entity_array]
  format_rows = ',\n'.join([SQL.Query.format_array(r) for r in rows])

  merge_query = SQL.MergeQuery(
    join_columns=['channel', entity.id_column_name],
    update_columns=[*entity.tag_column_names, 'upload_group'],
    source_table=entity.temp_tag_table_name,
    target_table=entity.target_tag_table_name,
    source_schema=None,
    target_schema=company_identifier
  )

  return SQL.Query(f'''
create temp table {entity.temp_tag_table_name} (like {company_identifier}.{entity.target_tag_table_name});
insert into {entity.temp_tag_table_name} (company_identifier, app, channel, {entity.id_column_name}, {','.join(entity.tag_column_names)}, upload_group)
values {format_rows};
{merge_query.query};
drop table {entity.temp_tag_table_name};
  ''',
    substitution_parameters=tuple(itertools.chain.from_iterable(rows)) + merge_query.substitution_parameters
  )

def subtag_entities_query(company_identifier: str, entity: Entity, entity_array: List[Dict[str, any]], subtag: str) -> SQL.Query:
  upload_group = 'almacen_api {date}'.format(date=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
  rows = [[company_identifier, c['app'], c['channel'], str(c[entity.id_column_name]), subtag, upload_group] for c in entity_array]
  format_rows = ',\n'.join([SQL.Query.format_array(r) for r in rows])

  merge_query = SQL.MergeQuery(
    join_columns=['channel', entity.id_column_name],
    update_columns=[entity.subtag_column_name, 'upload_group'],
    source_table=entity.temp_tag_table_name,
    target_table=entity.target_tag_table_name,
    source_schema=None,
    target_schema=company_identifier
  )

  return SQL.Query(f'''
create temp table {entity.temp_tag_table_name} (like {company_identifier}.{entity.target_tag_table_name});
insert into {entity.temp_tag_table_name} (company_identifier, app, channel, {entity.id_column_name}, {entity.subtag_column_name}, upload_group)
values {format_rows};
{merge_query.query};
drop table {entity.temp_tag_table_name};
  ''',
    substitution_parameters=tuple(itertools.chain.from_iterable(rows)) + merge_query.substitution_parameters
  )

def primary_tag_entities_query(company_identifier: str, entity: Entity, entity_array: List[Dict[str, any]], tag: str) -> SQL.Query:
  upload_group = 'almacen_api {date}'.format(date=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
  rows = [[company_identifier, c['app'], c['channel'], str(c[entity.id_column_name]), tag, upload_group] for c in entity_array]
  format_rows = ',\n'.join([SQL.Query.format_array(r) for r in rows])

  merge_query = SQL.MergeQuery(
    join_columns=['channel', entity.id_column_name],
    update_columns=[entity.primary_tag_column_name, 'upload_group'],
    source_table=entity.temp_tag_table_name,
    target_table=entity.target_tag_table_name,
    source_schema=None,
    target_schema=company_identifier
  )

  return SQL.Query(f'''
create temp table {entity.temp_tag_table_name} (like {company_identifier}.{entity.target_tag_table_name});
insert into {entity.temp_tag_table_name} (company_identifier, app, channel, {entity.id_column_name}, {entity.primary_tag_column_name}, upload_group)
values {format_rows};
{merge_query.query};
drop table {entity.temp_tag_table_name};
  ''',
    substitution_parameters=tuple(itertools.chain.from_iterable(rows)) + merge_query.substitution_parameters
  )

def delete_tag_entities_query(company_identifier: str, entity: Entity, entities_array: List[Dict[str, any]]) -> SQL.Query:
  rows = [[c['channel'], str(c[entity.id_column_name])] for c in entities_array]
  formatted_rows = ',\n'.join([SQL.Query.format_array(r) for r in rows])
  return SQL.Query(f'''
delete from {company_identifier}.{entity.target_tag_table_name}
where (channel, {entity.id_column_name}) in ({formatted_rows});
  ''', 
    substitution_parameters=tuple(itertools.chain.from_iterable(rows))
  )

def update_cube_entity_tags_query(company_identifier: str, entity: Entity) -> SQL.Query:
  return SQL.Query(f'''
begin transaction;
update {company_identifier}.performance_cube_filtered
set {', '.join(f'{c} = null' for c in entity.tag_column_names)};

update {company_identifier}.performance_cube_filtered
set {', '.join(f'{c} = t.{c}' for c in entity.tag_column_names)}
from {company_identifier}.{entity.target_tag_table_name} as t
where {company_identifier}.performance_cube_filtered.channel = t.channel
and {company_identifier}.performance_cube_filtered.{entity.id_column_name} = t.{entity.id_column_name};
end transaction;
  '''
  )

# DEPRECATED
# TODO remove this when longcat_ux is updated
@tags_blueprint.route('', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def tag_entities(identifier, entity_type):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  body = api.valid_body_from_request(
    request=flask.request,
    schema=tag_validation.patch_schema(entity)
  )
  query = tag_entities_query(
    company_identifier=identifier,
    entity=entity,
    entity_array=body[entity.plural],
    tag=body['tag'],
    subtag=body['subtag'] if 'subtag' in body else None
  )
  return api.run_query(query)

@tags_blueprint.route('/primary', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def primary_tag_entities(identifier, entity_type):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  body = api.valid_body_from_request(
    request=flask.request,
    schema=tag_validation.patch_primary_tag_schema(entity)
  )
  query = primary_tag_entities_query(
    company_identifier=identifier,
    entity=entity,
    entity_array=body[entity.plural],
    tag=body['tag'],
  )
  return api.run_query(query)

@tags_blueprint.route('/subtag', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def subtag_entities(identifier, entity_type):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  body = api.valid_body_from_request(
    request=flask.request,
    schema=tag_validation.patch_subtag_schema(entity)
  )
  query = subtag_entities_query(
    company_identifier=identifier,
    entity=entity,
    entity_array=body[entity.plural],
    subtag=body['subtag']
  )
  return api.run_query(query)


@tags_blueprint.route('/delete', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def delete_tags(identifier, entity_type):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  body = api.valid_body_from_request(
    request=flask.request,
    schema=tag_validation.delete_schema(entity)
  )
  query = delete_tag_entities_query(
    company_identifier=identifier,
    entity=entity,
    entities_array=body[entity.plural]
  )
  return api.run_query(query)

@tags_blueprint.route('/csv/merge', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def merge_tags_csv(identifier: str, entity_type: str):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  file = api.get_file(key='csv_file')
  tagger = Tagger()
  applied_count = tagger.apply_tags(
    schema_name=identifier,
    entity_name=entity.value,
    should_drop=False,
    should_purge=True,
    csv_stream=file,
    file_name=file.filename
  )
  return flask.jsonify({
    'success': applied_count > 0,
    'message': f'{applied_count} tags applied.',
  })

@tags_blueprint.route('/update/cube', methods=['PATCH'])
@api.check_privileges([AlmacenAPI.Privilege.tagger])
def update_cube(identifier, entity_type):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  query = update_cube_entity_tags_query(
    company_identifier=identifier,
    entity=entity
  )
  return api.run_query(query)
