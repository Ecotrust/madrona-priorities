# Install madrona et. al. into virtual environment 

```
virtualenv --system-site-packages env
cd env/
source bin/activate
cd src/
git clone https://github.com/Ecotrust/madrona.git
pip install -r src/madrona/requirements.txt
pip install --upgrade --force-reinstall requirements.txt
```

# Create and populate database

```
dropdb juniper -U postgres
createdb juniper -U postgres
python manage.py syncdb
python manage.py migrate
python manage.py enable_sharing --all
python manage.py loaddata fixtures/flatblocks.json
python manage.py loaddata seak/fixtures/base_data.json 
```

# edit seak/import.sh to point to data

```
sh seak/import.sh
```

# See docs/* for more info on importing, caching, deployment, etc

* create logs dir
* edit `deploy/wsgi.py`
* create apache vhost file
