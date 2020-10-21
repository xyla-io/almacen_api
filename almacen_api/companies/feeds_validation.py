crate_table_schema = {
  'type': 'object',
  'properties': {
    'column_types': {
      'type': 'object',
      'minLength': 1,
      'additionalProperties': {
        'type': 'string',
        'minLength': 1
      },
      'maxProperties': 1024
    },
    'read_only_groups': {
      'type': 'array',
      'items': {
        'type': 'string',
        'minLength': 0,
      }
    }
  },
  'requiredProperties': ['column_types'],
  'additionalProperties': False,
}

merge_table_data_schema = {
  'type': 'object',
  'properties': {
    'merge_column_names': {
      'type': 'array',
      'items': {
        'type': 'string',
        'minLength': 1,
      }
    }
  },
  'requiredProperties': ['merge_column_names'],
  'additionalProperties': False,
}