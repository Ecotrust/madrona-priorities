# Install madrona et. al. into virtual environment 

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
