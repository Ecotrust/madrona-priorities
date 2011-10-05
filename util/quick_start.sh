#!/bin/sh
echo " YOU MUST HAVE THE CORRECT SRID IN YOUR postgres database template1.  Got it?"
#In [1]: from django.contrib.gis.utils import add_postgis_srs as aps
#In [2]: aps(99997)
#In [3]: aps(99999)
read gotit

echo "dropdb"
dropdb watersheds -U postgres
echo "createdb"
createdb watersheds -U postgres

echo "select spatial ref sys"
psql -d watersheds -U postgres -c "select * from spatial_ref_sys where srid=99997;"

echo "syncdb"
python ../wp/manage.py syncdb
echo "migrate"
python ../wp/manage.py migrate
echo "Create study region"
python ../wp/manage.py create_study_region ../data/focal_studyregion.shp --name="Focal Region" 
python ../wp/manage.py change_study_region 1
echo "enable sharing"
python ../wp/manage.py enable_sharing --all
echo "change site"
python ../wp/manage.py site wp.hestia.ecotrust.org
echo "public kml"
python ../wp/manage.py loaddata ../wp/fixtures/public_kml.json
