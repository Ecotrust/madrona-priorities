var map;
var hilites;
var pu_layer;
var markers;
var selectFeatureControl;
var keyboardControl;
var selectGeographyControl;

function getCfFields() {
    // Find the set of conservation features represented in ALL of the selected planning units.
    if (pu_layer.selectedFeatures.length >= 1) {
        var tmpList = pu_layer.selectedFeatures[0].attributes.cf_fields;
        $.each( pu_layer.selectedFeatures, function(idx, feat) { 
            fieldList = feat.attributes.cf_fields;
            tmpList = tmpList.intersect(fieldList); 
        });
        return tmpList;
    } else { 
        return [];
    }
}

function getCostFields() {
    // Find the set of costs represented in ALL of the selected planning units.
    if (pu_layer.selectedFeatures.length >= 1) {
        var tmpList = pu_layer.selectedFeatures[0].attributes.cost_fields;
        $.each( pu_layer.selectedFeatures, function(idx, feat) { 
            fieldList = feat.attributes.cost_fields;
            tmpList = tmpList.intersect(fieldList); 
        });
        return tmpList;
    } else { 
        return [];
    }
}

function init_map() {
    map = new OpenLayers.Map({
        div: "map",
        projection: "EPSG:900913",
        displayProjection: "EPSG:4326",
        controls: [
            new OpenLayers.Control.Navigation(),
            new OpenLayers.Control.Zoom(),
            new OpenLayers.Control.LayerSwitcher({
                'div': OpenLayers.Util.getElement('layerswitcher')
            })
        ],
        minZoomLevel: 3,
        restrictedExtent: new OpenLayers.Bounds(-19140016, 2626698, -10262137, 11307047),
        numZoomLevels: 6
    });

    markers = new OpenLayers.Layer.Markers( "Markers", {displayInLayerSwitcher: false});

    var osm = new OpenLayers.Layer.OSM();

    var esri_physical = new OpenLayers.Layer.XYZ( "ESRI World Physical Map",
        "http://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var esri_shade = new OpenLayers.Layer.XYZ( "ESRI Shaded Relief Map",
        "http://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var esri_topo = new OpenLayers.Layer.XYZ( "ESRI World Topo Map",
        "http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var pu_utfgrid = new OpenLayers.Layer.UTFGrid({
         url: "/tiles/utfgrid/${z}/${x}/${y}.json", //dynamic, use once mapnik is figured out
         //url: "/media/tiles/planning_units/${z}/${x}/${y}.json",
         utfgridResolution: 4,
         sphericalMercator: true,
         displayInLayerSwitcher: false
        } 
    );

    var pu_tiles = new OpenLayers.Layer.OSM( "Planning Units",
        "/tiles/planning_units/${z}/${x}/${y}.png",
        {
         sphericalMercator: true,
         isBaseLayer: false
        } 
    );

    var google_terrain = new OpenLayers.Layer.Google(
        "Google Terrain",
        {type: google.maps.MapTypeId.TERRAIN, opacity: 0.6}
    );

    var myStyles = new OpenLayers.StyleMap({
        "default": new OpenLayers.Style({
            display: "none",  /* needs to be set temporarily to true for selection to work */
            strokeWidth: 0,
            fillOpacity: 0
        }),
        "select": new OpenLayers.Style({
            display: true,
            strokeWidth: 0,
            fillColor: "#ffff00",
            fillOpacity: 0.5,
            graphicZIndex: 2
        }),
        "select_geography": new OpenLayers.Style({
            display: true,
            fillColor: "#777777",
            fillOpacity: 0.5
        })
    });

    // allow testing of specific renderers via "?renderer=Canvas", etc
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
    pu_layer = new OpenLayers.Layer.Vector("Planning Units", {
        styleMap: myStyles,
        renderers: renderer,
        displayInLayerSwitcher: false
    });

    var url = "/seak/planning_units.geojson";
    var jqxhr = $.ajax({
        url: url, 
        cache: true,
        dataType: 'json', 
        success: function(data) {
            var gformat = new OpenLayers.Format.GeoJSON();
            try {
                var feats = gformat.read(data); 
                pu_layer.addFeatures(feats);
            } catch(err) {
                console.log(err.message);
                app.scenarios.viewModel.planningUnitsLoadError(true);
            }
        }
    })
    .error(function() { app.scenarios.viewModel.planningUnitsLoadError(true); })
    .complete(function() { app.scenarios.viewModel.planningUnitsLoadComplete(true); });

    map.addLayers([esri_shade, esri_topo, esri_physical, osm, google_terrain, pu_layer, pu_tiles, pu_utfgrid, markers]);

    map.isValidZoomLevel = function(zoomLevel) {
        // Why is this even necessary OpenLayers?.. grrr
        // http://stackoverflow.com/questions/4240610/min-max-zoom-level-in-openlayers
        return ( (zoomLevel !== null) &&
            (zoomLevel >= this.minZoomLevel) &&
            (zoomLevel < this.minZoomLevel + this.numZoomLevels));
    };
    
    selectFeatureControl = new OpenLayers.Control.SelectFeature(
        pu_layer,
        {
            multiple: true
        }
    );

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
    );

    keyboardControl = new OpenLayers.Control.KeyboardDefaults();

    selectFeatureControl.deactivate();
    keyboardControl.deactivate();
    selectGeographyControl.deactivate();
    map.addControls([selectFeatureControl, selectGeographyControl, keyboardControl]);

    var lookup_url = "/seak/field_lookup.json";
    var fieldLookup;
    var xhr = $.ajax({
        url: lookup_url, 
        cache: true,
        dataType: 'json', 
        success: function(data) { fieldLookup = data; }
    })
    .error( function() { 
        fieldLookup = null; 
    });

    var callback = function(infoLookup) {
        var msg = ""; 
        var puname = ""; 
        $("#info").hide();
        var fnc = function(idx, val) {
            var varname = fieldLookup[idx];
            if (val >= 0 && varname) { // Assume negative is null
                try {
                    msg += "<tr><th width=\"75%\">"+ varname + "</th><td>" + val.toPrecision(6) + "</td></tr>";
                } catch (err) {
                    msg += "<tr><th width=\"75%\">"+ varname + "</th><td>" + val + "</td></tr>";
                }
            } else if(idx.toLowerCase() == "name") {
                puname = val;
            }

        };
        if (infoLookup) {
            var info;
            for (var idx in infoLookup) {
                info = infoLookup[idx];
                if (info && info.data) {
                    msg = "<table class=\"table table-condensed\">";
                    $.each(info.data, fnc);
                    msg += "</table>";
                    $("#info").show();
                }
            }
        }
        $("#info-title").html("<h4>" + puname + "</h4>");
        $("#info-content").html(msg);
    };

    var ctl = new OpenLayers.Control.UTFGrid({
        callback: callback,
        handlerMode: "click"
    });

    map.addControl(ctl);

    map.setCenter(new OpenLayers.LonLat(-15400000, 6700000), 4);
}