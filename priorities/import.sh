DATA_DIR=~/projects/BLM_Aquatics/data_20121210
python manage.py import_planning_units \
    $DATA_DIR/HUC10_BLM_20121210_simple.shp \
    $DATA_DIR/BLM_metrics20121210.xls \
    $DATA_DIR/HUC10_BLM_20121210.shp

