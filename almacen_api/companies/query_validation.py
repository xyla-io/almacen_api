post_run_schema = {
  'type': 'object',
  'properties': {
    'query': {
      'type': 'string',
      'minLength': 1,
    },
  },
  'requiredProperties': ['query'],
  'additionalProperties': False,
}