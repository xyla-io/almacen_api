import flask

from data_layer import Redshift as SQL
from ..api import api, AlmacenAPI
from enum import Enum
from typing import Optional

entities_blueprint = flask.Blueprint('companies_entities', __name__, url_prefix='/companies/<identifier>/entities')

class Entity(Enum):
  keyword = 'keyword'
  ad = 'ad'
  adset = 'adset'
  campaign = 'campaign'

  @classmethod
  def from_plural(cls, value):
    for entity in Entity:
      if entity.plural == value:
        return entity
    
    raise ValueError('Unsupported value', value)

  @property
  def plural(self) -> str:
    return f'{self.value}s'

  @property
  def source_table_name(self) -> str:
    return f'entity_{self.value}'
  
  @property
  def target_tag_table_name(self) -> str:
    return f'tag_{self.value}s'
  
  @property
  def temp_tag_table_name(self) -> str:
    return f'upload_{self.target_tag_table_name}'
  
  @property
  def id_column_name(self) -> str:
    return f'{self.value}_id'

  @property
  def primary_tag_column_name(self) -> str:
    return f'{self.value}_tag'

  @property
  def subtag_column_name(self) -> str:
    return f'{self.value}_subtag'
  
  @property
  def tag_column_names(self) -> str:
    return [self.primary_tag_column_name, self.subtag_column_name]

def get_entities_query(company_identifier: str, entity: Entity, app_identifier: Optional[str]=None, tag: Optional[str]=None) -> SQL.Query:
  query = f'select * from {company_identifier}.{entity.source_table_name}'
  conditional_keyword = 'where'

  if app_identifier is not None:
    query += f'\n{conditional_keyword} app_display_name = \'{app_identifier}\''
    conditional_keyword = 'and'
  if tag is not None:
    query += f'\n{conditional_keyword} {entity.value}_tag = \'{tag}\''
    conditional_keyword = 'and'

  return SQL.Query(query=query)

@entities_blueprint.route('/<entity_type>', methods=['GET'])
@api.check_privileges()
def fetch(identifier, entity_type):
  try:
    entity = Entity.from_plural(entity_type)
  except ValueError as error:
    raise AlmacenAPI.Error(code=400, message='Unsupported entity type.', error=error)

  query = get_entities_query(
    company_identifier=identifier,
    entity=entity,
    app_identifier=flask.request.args.get('app'),
    tag=flask.request.args.get('tag')
  )
  return api.run_query(query)