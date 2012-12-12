This document describes how to create initial deployments of a priorities tool on a remote server. 
After the initial deployment, you can use fabric (see `docs/updating.txt`) to update the remote server, 
import datasets, etc.

# Checkout the source

```
cd /usr/local/apps/
git clone git@github.com:Ecotrust/madrona-priorities.git <PROJECT_NAME> 
cd <PROJECT_NAME>
git checkout <PROJECT_NAME> 
```

# Install madrona et. al. into virtual environment 

```
virtualenv --system-site-packages env-<PROJECT_NAME>
source env-<PROJECT_NAME>/bin/activate
cd env-<PROJECT_NAME>/src
git clone https://github.com/Ecotrust/madrona.git
cd ../../
pip install -r env-<PROJECT_NAME>/src/madrona/requirements.txt
pip install --upgrade --force-reinstall -r requirements.txt
```

# Create and populate database

```
cd priorities
dropdb <PROJECT_NAME> -U postgres
createdb <PROJECT_NAME> -U postgres
# set up settings_local.py for DB and redis
python manage.py syncdb
python manage.py migrate
python manage.py enable_sharing --all
python manage.py loaddata fixtures/flatblocks.json
python manage.py loaddata fixtures/project_base_data.json 
```

# Apache

* edit `deploy/wsgi.py`
* edit `deploy/tilestache_wsgi.py`
* create apache vhost file based on the default
```
sed 's/APPNAME/<PROJECT_NAME>/' deploy/default.apache > /etc/apache2/sites-available/<PROJECT_NAME>.labs.ecotrust.org
touch MAINTENANCE_MODE
sudo a2ensite <PROJECT_NAME>.labs.ecotrust.org
sudo /etc/init.d/apache2 reload
```

# Next steps

See `docs/updating.txt`
