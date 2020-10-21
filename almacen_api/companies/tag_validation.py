from .entities import Entity
from typing import Dict

# DEPRECATED
# TODO remove this when longcat_ux is updated
def patch_schema(entity: Entity) -> Dict[str, any]:
  return {
    'type': 'object',
    'properties': {
      'tag': {
        'type': 'string',
        'minLength': 1,
      },
      'subtag': {
        'type': 'string',
        'minLength': 1,
      },
      f'{entity.value}s': {
        'type': 'array',
        'items': {
          'type': 'object',
          'properties': {
            'app': {
              'type': 'string',
              'minLength': 1,
            },
            'channel': {
              'type': 'string',
              'minLength': 1,
            },
            entity.id_column_name: {
              'type': 'string',
              'minLength': 1,
            },
          },
          'required': ['app', 'channel', entity.id_column_name],
          'additionalProperties': False,
        },
        'minItems': 1,
      },
    },
    'required': ['tag', f'{entity.value}s'],
    'additionalProperties': False,
  }


def patch_primary_tag_schema(entity: Entity) -> Dict[str, any]:
  return {
    'type': 'object',
    'properties': {
      'tag': {
        'type': 'string',
        'minLength': 1,
      },
      f'{entity.value}s': {
        'type': 'array',
        'items': {
          'type': 'object',
          'properties': {
            'app': {
              'type': 'string',
              'minLength': 1,
            },
            'channel': {
              'type': 'string',
              'minLength': 1,
            },
            entity.id_column_name: {
              'type': 'string',
              'minLength': 1,
            },
          },
          'required': ['app', 'channel', entity.id_column_name],
          'additionalProperties': False,
        },
        'minItems': 1,
      },
    },
    'required': ['tag', f'{entity.value}s'],
    'additionalProperties': False,
  }

def patch_subtag_schema(entity: Entity) -> Dict[str, any]:
  return {
    'type': 'object',
    'properties': {
      'subtag': {
        'type': 'string',
        'minLength': 1,
      },
      f'{entity.value}s': {
        'type': 'array',
        'items': {
          'type': 'object',
          'properties': {
            'app': {
              'type': 'string',
              'minLength': 1,
            },
            'channel': {
              'type': 'string',
              'minLength': 1,
            },
            entity.id_column_name: {
              'type': 'string',
              'minLength': 1,
            },
          },
          'required': ['app', 'channel', entity.id_column_name],
          'additionalProperties': False,
        },
        'minItems': 1,
      },
    },
    'required': ['subtag', f'{entity.value}s'],
    'additionalProperties': False,
  }

def delete_schema(entity: Entity) -> Dict[str, any]:
  return {
    'type': 'object',
    'properties': {
      f'{entity.value}s': {
        'type': 'array',
        'items': {
          'type': 'object',
          'properties': {
            'channel': {
              'type': 'string',
              'minLength': 1,
            },
            entity.id_column_name: {
              'type': 'string',
              'minLength': 1,
            },
          },
          'required': ['channel', entity.id_column_name],
          'additionalProperties': False,
        },
        'minItems': 1,
      },
    },
    'required': [f'{entity.value}s'],
    'additionalProperties': False,
  }