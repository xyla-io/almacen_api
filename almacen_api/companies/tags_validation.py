from typing import Dict
from enum import Enum

class ParseMethod(Enum):
  sequence = 'sequence'
  switch = 'switch'
  parser = 'parser'

def parse_schema(parse_method: ParseMethod) -> Dict[str, any]:
  return {
    'type': 'object',
    'properties': {
      'names': {
        'type': 'array',
        'minLength': 1,
        'items': {
          'type': 'string',
        },
      },
      'delimiter': {
        'type': 'string',
        'minLength': 1,
      },
      **({
        'index': {
          'type': 'integer',
        },
      } if parse_method is ParseMethod.switch else {
        'indices': {
          'type': 'array',
          'items': {
            'type': 'integer',
          },
        },
        'labels': {
          'type': 'object',
          'patternProperties': {
            '^-?[0-9]+$': {
              'type': 'string',
            },
          },
          'additionalProperties': False,
        },        
      })
    },
    'required': [
      'names',
      'delimiter',
      *(['index'] if parse_method is ParseMethod.switch else []),
    ],
    'additionalProperties': False,
  }

def update_schema() -> Dict[str, any]:
  return {
    'type': 'object',
    'properties': {
      'tags': {
        'type': 'array',
        'minItems': 1,
        'items': {
          'type': 'object',
          'properties': {
            'url': {
              'type': 'string',
              'minLength': 1,
              'maxLength': 256,
            },
            'key': {
              'type': 'string',
              'minLength': 1,
              'maxLength': 64,
            },
            'value': {
              'type': ['string', 'null'],
              'maxLength': 64,
            },
            'flags': {
              'type': 'integer',
              'minimum': 0,
            },
            'set': {
              'type': 'string',
            },
          },
          'required': ['url', 'key', 'value'],
          'additionalProperties': False,
        }
      },
    },
    'required': ['tags'],
    'additionalProperties': False,
  }

def update_parser_schema() -> Dict[str, any]:
  return {
    'type': 'object',
    'additionalProperties': False,
    'required': ['key_map'],
    'properties': {
      'name': {
        'type': 'string',
        'pattern': r'[a-zA-Z0-9]+',
      },
      'url': {
        'type': 'string',
      },
      'key_map': {
        'type': 'object',
        'required': ['map'],
        'properties': {
          'map': {
            'type': 'string',
            'enum': ['iomap.io_channel.parse/IOSequenceParser', 'iomap.io_channel.parse/IORegexParser', 'iomap.io_channel.parse/IOSwitchParser']
          },
        },
      },
    },
  }

def update_parser_key_map_schema(map_type: str) -> Dict[str, any]:
  schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['map'],
    'properties': {
      'map': {
        'type': 'string',
        'enum': [map_type]
      },
    },
  }
  if map_type == 'iomap.io_channel.parse/IOSequenceParser':
    schema['properties'].update({
      'construct': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['delimiter'],
        'properties': {
          'delimiter': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 1024,
          },
          'targets': {
            'type': 'array',
            'maxLength': 1024,
            'items': {
              'type': 'object',
              'additionalProperties': False,
              'required': ['index'],
              'properties': {
                'index': {
                  'type': 'integer',
                },
                'label': {
                  'type': 'string',
                  'maxLength': 1024,
                },
              },
            },
          },
        },
      },
    })
  elif map_type == 'iomap.io_channel.parse/IORegexParser':
    schema['properties'].update({
      'construct': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['targets'],
        'properties': {
          'targets': {
            'type': 'array',
            'maxLength': 1024,
            'items': {
              'type': 'object',
              'additionalProperties': False,
              'required': ['pattern'],
              'properties': {
                'pattern': {
                  'type': 'string',
                  'maxLength': 1024,
                },
                'replacement': {
                  'type': 'string',
                  'maxLength': 1024,
                },
                'label': {
                  'type': 'string',
                  'maxLength': 1024,
                },
              },
            },
          },
        },
      },
    })
  elif map_type == 'iomap.io_channel.parse/IOSwitchParser':
    schema['properties'].update({
      'construct': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['parser_identifier_key_map'],
        'properties': {
          'parser_identifier_key_map': {
            'type': 'object',
            'additionalProperties': False,
            'required': ['map'],
            'properties': {
              'iokeymap': {
                'type': 'string',
                'minLength': 1,
              },
              'output': {
                'additionalProperties': False,
                'required': ['run.parser_identifier'],
                'properties': {
                  'run.parser_identifier': {
                    'type': 'string',
                  },
                },
              },
            },
          },
          'parser_provider_key_map': {
            'type': 'string',
            'enum': ['iokeymap.parser_provider'],
          },
        },
      },
    })
  return schema

def parser_parse_schema() -> Dict[str, any]:
  return {
    'type': 'object',
    'additionalProperties': False,
    'required': ['names'],
    'properties': {
      'names': {
        'type': 'array',
        'minLength': 1,
        'items': {
          'type': 'string',
        },
      },
    },
  }

def parser_update_tags_schema() -> Dict[str, any]:
  return {
    'type': 'object',
    'additionalProperties': False,
    'required': ['urls_to_names'],
    'properties': {
      'urls_to_names': {
        'type': 'object',
        'maxProperties': 65536,
        'additionalProperties': {
          'type': 'string',
          'maxLength': 65536,
        },
      },
      'update_mode': {
        'type': 'string',
        'enum': ['tag', 'url', 'dry_run']
      },
    },
  }
