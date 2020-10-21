import os
import sys

configuration_name = sys.argv[1]
os.environ['ALMACEN_API_CONFIGURATION'] = configuration_name

from almacen_api import app, api

if 'run' in api.configuration:
  app.run(**api.configuration['run'])
else:
  app.run()