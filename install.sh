#!/bin/bash

set -e
set -x

git submodule update --init
rm -rf venv
python3.7 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cd development_packages
for DEVPKG in data_layer moda subir io_map io_channel io_almacen
do
  cd $DEVPKG
  if [ -f requirements.txt ]; then
    pip install -r requirements.txt
  fi
  python setup.py develop
  cd ..
done
cd ..

deactivate
if [ ! -d development_packages/subir/config ]; then
  ln -s ../../config development_packages/subir/config
fi
