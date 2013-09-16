DATA_DIR=./data/data_20130820
python manage.py import_planning_units \
    $DATA_DIR/HUC10_BLM_20130812_simple.shp \
    $DATA_DIR/BLM_metrics20130812.xls \
    $DATA_DIR/HUC10_BLM_20130812_WGS.shp

