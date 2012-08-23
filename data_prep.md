# Prepping data for the priorities tool

You will need a polygon/multi-polygon shapefile representing your planning units.
This shapefile must be prepared for the tool according to the following steps:

## Attributes check
- Conservation Features and Costs must be represented by numeric attribute fields
- Numeric fields must differentiate between zero (no habitat), a positive number (some measure of habitat) 
    and a negative null value (eg `-999` representing no information for that planning unit). 
    Negative non-null values are not valid.
- dat20120821_Merc.shp must contain at least one integer field for the feature id. this must be unique.
- Data must contain at least one Text field for the planning unit name (cannot be numeric!)

## Data processing
- Shapefile must be reprojected to Spherical Mercator for compatibility 
    with web mapping systems. If you need area, you should calculate that as 
    an attribute field in an equal area projection before this step.
    From ArcGIS, use the projection named `WGS_1984_Web_Mercator_Auxiliary_Sphere`. 
    Use `EPSG: 3857` with proj. For example, the `ogr2ogr` the command would be:
        `ogr2ogr -t_srs epsg:3857 planning_units_mercator.shp planning_units.shp planning_units`

- For performance purposes, it can help to simplify the layer to reduce vertices. 
    It is highly recomended to simplify AFTER necessary changes to the attribute table are completed.
    Make sure that the simplification technique maintains topology (i.e. doesnt leave gaps between polygons).
    ArcGIS uses a `RESOLVE_ERRORS` flag in the `Simplify Polygon` tool. 
    The NPLCC data is simplified to a tolerance of 2100 meters to smooth out the 2km raster artifacts.

## Metadata
- Complete the xls metadata file describing the dataset:
    - ConservationFeatures and Costs must describe the dbf fieldname used, units, unique names and ids. 
    - PlanningUnit names and fids and null values
    - Fields can define named geographies (e.g. Southeast Alaska is defined by all planning units where `SpePar` field is not null)

## Loading
- Upload data to the server
- Run the import procedure:
```
 python manage.py import_planning_units \
   ~/projects/nplcc/data_20120822/H1K_Values20120821_Merc.shp \
   ~/projects/nplcc/data_20120822/NPLCC_metrics20120822.xls \
   ~/projects/nplcc/data_20120822/H1K_Values20120821_Merc_Simp.shp
```
