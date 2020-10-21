almacen_api_config = {
  'debug': {
    'name': 'almacen_api',
    'database': 'stage_01',
    'debug': True,
    'app': {
      'DEBUG': True,
      'UPLOAD_FOLDER': '/tmp',
    },
    'run': {
      # 'ssl_context': ('ssl/cert.pem', 'ssl/key.pem'),
      'port': 8000,
    },
    'app_tokens': {
      'TOKEN': {
        'app': 'development',
        'roles': ['super', 'tagger'],
      },
      'TOKEN': {
        'app': 'longcat_api',
        'roles': ['tagger'],
      },
    },
  },
  'development': {
    'name': 'almacen_api',
    'database': 'stage_01',
    'run': {
      'port': 8000,
    },
    'app_tokens': {
      'TOKEN': {
        'app': 'development',
        'roles': ['super', 'tagger'],
      },
      'TOKEN': {
        'app': 'longcat_api',
        'roles': ['tagger'],
      },
      'TOKEN': {
        'app': 'longcat_api',
        'roles': ['reader'],
      },
    },
    's3_query_results_bucket': {
      'access_key_id': 'ACCESSKEY',
      'secret_access_key': 'SECRET',
      'bucket_name': 'almacen-entrega',
      'bucket_region': 'us-east-2',
      'bucket_directory': 'almacen_api/stage/query_results',
    },
  },
  'production': {
    'name': 'almacen_api',
    'database': 'prod_01',
    'app_tokens': {
      'TOKEN': {
        'app': 'longcat_api',
        'roles': ['tagger'],
      },
    },
  },
  'testing': {
    'name': 'almacen_api_test',
    'database': 'stage_01',
    'app_tokens': {
      'TOKEN': {
        'app': 'development',
        'roles': ['super', 'tagger'],
      },
    },
  },
}