#!/bin/bash
DB="usfw2"

createdb -T gis_template $DB
python manage.py syncdb --noinput
