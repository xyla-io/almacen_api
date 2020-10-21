import importlib

def import_config(name: str):
  try:
    module = importlib.import_module('config.local_{}_config'.format(name))
  except Exception:
    module = importlib.import_module('config.{}_config'.format(name))
  return getattr(module, '{}_config'.format(name))

almacen_api_config = import_config('almacen_api')
sql_config = import_config('sql')