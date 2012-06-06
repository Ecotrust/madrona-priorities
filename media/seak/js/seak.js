var map;
var hilites;
var pu_layer;
var selectFeatureControl;
var selectGeographyControl;

function init_map() {
    map = new OpenLayers.Map({
        div: "map",
        projection: "EPSG:900913",
        displayProjection: "EPSG:4326",
        numZoomLevels: 18
    });
    map.addControl(new OpenLayers.Control.LayerSwitcher({
        'div': OpenLayers.Util.getElement('layerswitcher')
    }));

    map.addControl(new OpenLayers.Control.KeyboardDefaults() );

    var osm = new OpenLayers.Layer.OSM();

    var terrain = new OpenLayers.Layer.OSM("Terrain", 
        "http://tile.stamen.com/terrain/${z}/${x}/${y}.jpg",
        {sphericalMercator: true} 
    );
 
    var esri_physical = new OpenLayers.Layer.XYZ( "ESRI World Physical Map",
        "http://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var esri_shade = new OpenLayers.Layer.XYZ( "ESRI Shaded Relief Map",
        "http://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var google_terrain = new OpenLayers.Layer.Google(
        "Google Terrain",
        {type: google.maps.MapTypeId.TERRAIN, opacity: 0.6}
    );

    var myStyles = new OpenLayers.StyleMap({
        "default": new OpenLayers.Style({
            fillColor: "#ffffff",
            fillOpacity: 0.4,
            strokeColor: "#003300",
            strokeWidth: 0.3,
            graphicZIndex: 1
        }),
        "select": new OpenLayers.Style({
            fillColor: "#ffff00",
            fillOpacity: 0.6,
            graphicZIndex: 2
        }),
        "select_geography": new OpenLayers.Style({
            fillColor: "#3333ff",
            fillOpacity: 0.6,
            graphicZIndex: 3
        })
    });

    // allow testing of specific renderers via "?renderer=Canvas", etc
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
    pu_layer = new OpenLayers.Layer.Vector("Planning Units", {
        styleMap: myStyles,
        renderers: renderer
    });

    var url = "/seak/planning_units.geojson";

    var jqxhr = $.get(url, function(data) {
        var gformat = new OpenLayers.Format.GeoJSON();
        try {
            var feats = gformat.read(data); 
            pu_layer.addFeatures(feats);
        } catch(err) {
            console.log(err.message);
            app.scenarios.viewModel.planningUnitsLoadError(true);
        }
    }, 'json')
    .error(function() { app.scenarios.viewModel.planningUnitsLoadError(true); })
    .complete(function() { app.scenarios.viewModel.planningUnitsLoadComplete(true); })



    map.addLayers([esri_shade, esri_physical, osm, google_terrain, terrain, pu_layer]);
    
    selectFeatureControl = new OpenLayers.Control.SelectFeature(
        pu_layer,
        {
            multiple: true
        }
    )

    var geographySelectCallback = function(){ 
        $('#geographySelectionCount').html(pu_layer.selectedFeatures.length);
    };

    selectGeographyControl = new OpenLayers.Control.SelectFeature(
        pu_layer,
        {
            clickout: true, 
            toggle: false,
            multiple: true, 
            hover: false,
            toggleKey: "ctrlKey", // ctrl key removes from selection
            multipleKey: "shiftKey", // shift key adds to selection
            renderIntent: "select_geography",
            box: true,
            onSelect: geographySelectCallback,
            onUnselect: geographySelectCallback
        }
    )
    selectFeatureControl.deactivate();
    selectGeographyControl.deactivate();
    map.addControls([selectFeatureControl, selectGeographyControl]);

    map.setCenter(new OpenLayers.LonLat(-13600000, 6700000), 4);
}
