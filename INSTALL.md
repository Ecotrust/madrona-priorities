* Install Madrona
* Create and populate db

```
dropdb nplcc -U postgres
createdb nplcc -U postgres
python manage.py syncdb
python manage.py migrate
python manage.py enable_sharing --all
python manage.py loaddata fixtures/flatblocks.json
python manage.py import_planning_units data/hydro1k_nplcc_merc_join_simp2100.shp data/hydro1k_nplcc_meta.xls
```
