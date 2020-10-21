import os

try:
  os.environ['ALMACEN_API_CONFIGURATION']
except:
  os.environ['ALMACEN_API_CONFIGURATION'] = 'development'

from almacen_api import app
