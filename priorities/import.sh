DATA_DIR=/usr/local/apps/juniper-blm/priorities/data/data_10172012
python manage.py import_planning_units \
    $DATA_DIR/HUC5_final_11_merc_simple250m.shp \
    $DATA_DIR/JUNIPERBLM_metrics20121017_MARXAN.xls \
    $DATA_DIR/HUC5_final_11_merc.shp

