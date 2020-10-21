#!/bin/bash
source venv/bin/activate
DEFAULT_CONFIG='development'
[[ -n $1 ]] && DEFAULT_CONFIG=$1
ALMACEN_API_CONFIGURATION=$DEFAULT_CONFIG gunicorn -t 600 serve:app
