DATA_DIR=data/data_10172012
python manage.py import_planning_units \
    $DATA_DIR/HUC5_final_11_merc.shp \
    $DATA_DIR/JUNIPERBLM_metrics20121017_MARXAN.xls
