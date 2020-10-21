# almacen_api

## Install

### Install Python virtual environment

```bash
# in the project root directory
./install.sh
```

## Run

Run using the commands:

```bash
# serve in production mode
./serve.sh
# run through Python with a specified configuration
source venv/bin/activate
python run.py development
```

## Daemonize

Use the `almacen_api.service` file as a template to daemonize the Almacén API with `systemd`. 

Modify the almacen_api.service template file, then copy it into the `/etc/systemd/system` directory.

```bash
# modify the file, replacing user and path placeholders
vi almacen_api.service
# as root, install the service
cp almacen_api.service /etc/systemd/system/
# start the service, and enable it at system startup
systemctl start almacen_api.service
systemctl enable almacen_api.service
# check the status
systemctl status almacen_api.service
# check that the gunicorn server is responding
curl http://127.0.0.1:8000
```