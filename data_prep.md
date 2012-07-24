# Prepping data for the priorities tool

You will need a polygon/multi-polygon shapefile representing your planning units.
This shapefile must be prepared for the tool according to the following steps:

## Attributes check
- Conservation Features and Costs must be represented by numeric attribute fields
- Numeric fields must differentiate between zero (no habitat), a positive number (some measure of habitat) 
    and a negative nuill value (eg `-999` representing no information for that planning unit)
- Data must contain at least one Integer field for the feature ID. This must be unique.
- Data must contain at least one Text field for the planning unit name (cannot be numeric!)

## Data processing
- Shapefile must be reprojected to Spherical Mercator for compatibility 
    with web mapping systems. If you need area, you should calculate that as 
    an attribute field in an equal area projection before this step.
    From ArcGIS, use the projection named `WGS_1984_Web_Mercator_Auxiliary_Sphere`. 
- For performance purposes, it can help to simplify the layer to reduce vertices. 
    Make sure that the simplification technique maintains topology (i.e. doesnt leave gaps between polygons).
    ArcGIS uses a `RESOLVE_ERRORS` flag in the `Simplify Polygon` tool. 
    The NPLCC data is simplified to 2100meters to smooth out the 2km raster artifacts.

## Metadata
- Complete the xls metadata file describing the dataset:
    - ConservationFeatures and Costs must describe the dbf fieldname used, units, unique names and ids. 
    - PlanningUnit names and fids and null values
    - Fields can define named geographies (e.g. Southeast Alaska is defined by all planning units where `SpePar` field is not null)

## Loading
- Upload data to the server
- Run the import procedure:
```
 python manage.py import_planning_units data/nplcc_20120712_merc_simplify2100.shp data/hydro1k_nplcc_meta_20120712.xls
 # optionally specify a third argument to provide a full-res shp for tiles.
```
