DATA_DIR=../data/local/ToolInputs20130822
python manage.py import_planning_units \
    $DATA_DIR/HUC8_20130206_merc_simple.shp \
    $DATA_DIR/USFWS_metrics20130822.xls \
    $DATA_DIR/HUC8_20130206_merc.shp

