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
    var latlon = new OpenLayers.Projection("EPSG:4326");
    var merc = new OpenLayers.Projection("EPSG:900913");
    var extent = new OpenLayers.Bounds(-125.04, 41.5, -116.0, 46.4);
    extent.transform(latlon, merc);

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
        zoom: 6,
        minZoomLevel: 6,
        restrictedExtent: extent, //new OpenLayers.Bounds(-19140016, 2626698, -10262137, 11307047),
        maxExtent: extent, //new OpenLayers.Bounds(-19140016, 2626698, -10262137, 11307047),
        numZoomLevels: 6
    });

    //var extent = new OpenLayers.Bounds(-157.8516, 33.7243, -112.8516, 65.0721);
    /*
    console.log(extent);
    map.setOptions({restrictedExtent: extent});
    */

    markers = new OpenLayers.Layer.Markers( "Markers", {displayInLayerSwitcher: false});

    var terrain = new OpenLayers.Layer.XYZ( "Mapbox Terrain",
        "http://d.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.png",
        {sphericalMercator: true} 
    );

    var esri_shade = new OpenLayers.Layer.XYZ( "ESRI Shaded Relief Map",
        "http://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var blue_marble = new OpenLayers.Layer.XYZ( "Blue Marble Satellite",
        //"http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/${z}/${y}/${x}",
        "http://c.tiles.mapbox.com/v3/mapbox.blue-marble-topo-bathy-jul/${z}/${x}/${y}.png",
        {sphericalMercator: true, opacity: 0.75} 
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
    pu_layer = new OpenLayers.Layer.Vector("Planning Unit Highlight", {
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

    map.addLayers([terrain, esri_shade, blue_marble, pu_layer, pu_tiles, pu_utfgrid, markers]);
    map.getLayersByName("Markers")[0].setZIndex(9999);
    map.zoomToMaxExtent();

    var lookup_url = "/seak/field_lookup.json";
    var fieldLookup;
    $('<div><input type="checkbox" id="layer-select-toggle"></input></div>')
        .appendTo('#layerswitcher')
        .attr("id", "layer-select-div");
    var sel = $('<select>').appendTo('#layer-select-div').attr("id","layer-select");
    sel.append($("<option>").attr('value','').text('.. Select attribute to map ..'));
    var xhr = $.ajax({
        url: lookup_url, 
        cache: true,
        dataType: 'json', 
        success: function(data) { 
            fieldLookup = data; 
            $.each(data, function(dbf_fieldname, realname) {
                map.addLayer( 
                    new OpenLayers.Layer.OSM( realname,
                        "/tiles/" + dbf_fieldname + "/${z}/${x}/${y}.png",
                        { visibility: false, 
                          sphericalMercator: true, 
                          displayInLayerSwitcher: false, 
                          isBaseLayer: false } 
                    )
                );
                sel.append($("<option>").attr('value',realname).text(realname));
            });
            // sort 'em
            var my_options = $("select#layer-select option");
            my_options.sort(function(a,b) {
                if (a.text > b.text) return 1;
                else if (a.text < b.text) return -1;
                else return 0;
            });
            sel.empty().append( my_options );
        }
    })
    .error( function() { 
        fieldLookup = null; 
    });
   
    // when the dropdown changes, tell openlayers
    var switchLayer = function() {
        var lyrname;
        $.each($("select#layer-select option"), function(k,v) {
            lyrname = $(v).val();
            if (lyrname !== '')
                map.getLayersByName(lyrname)[0].setVisibility(false);
        });
        lyrname = $("select#layer-select option:selected").val();
        if (lyrname !== '' && $('#layer-select-toggle').prop('checked')) {
            map.getLayersByName(lyrname)[0].setVisibility(true);
            map.getLayersByName('Planning Unit Highlight')[0].setVisibility(false);
            $('.map-legend-group').hide();
            $('#map-legend-attr').show();
        } else {
            map.getLayersByName('Planning Unit Highlight')[0].setVisibility(true);
            $('.map-legend-group').hide();
            $('#map-legend-scenario').show();
        }
    }

    $('#layer-select-toggle').bind('change', switchLayer);
    sel.bind('change', switchLayer);

    var sortByKeys = function(obj) {
        var tmpObj = {};
        var fullName;
        var keys = [];
        var i, k, len;
        var outObj = {};

        for(var key in obj) {
            fullName = fieldLookup[key];
            if (!fullName)
                fullName = key;
            tmpObj[fullName] = obj[key];
        }

        for(var key in tmpObj) {
            if(tmpObj.hasOwnProperty(key)) {
                keys.push(key);
            }
        }

        keys.sort();
        len = keys.length;
        for (i=0; i < len; i++) {
            k = keys[i];
            outObj[k] = tmpObj[k];
        }
        return outObj;
    };

    var utfgridCallback = function(infoLookup) {
        var msg = ""; 
        var puname = "Watershed Info"; 
        $("#info").hide();
        var fnc = function(idx, val) {
            if (val >= 0) { // Assume negative is null
                try {
                    msg += "<tr><th width=\"75%\">"+ idx + "</th><td>" + val.toPrecision(6) + "</td></tr>";
                } catch (err) {
                    msg += "<tr><th width=\"75%\">"+ idx + "</th><td>" + val + "</td></tr>";
                }
            } 
            if(idx.toLowerCase() == "name") { // assume "name" 
                puname = val;
            }
        };

        $.each(infoLookup, function(k, info) {
            if (info.data) {
                msg = "<table class=\"table table-condensed\">";
                $.each(sortByKeys(info.data), fnc);
                msg += "</table>";
                $("#info").show();
            }
        });
        $("#info-title").html("<h4>" + puname + "</h4>");
        $("#info-content").html(msg);
    };

    var ctl = new OpenLayers.Control.UTFGrid({
        callback: utfgridCallback,
        handlerMode: "click"
    });

    map.addControl(ctl);

    map.setCenter(new OpenLayers.LonLat(-15400000, 6700000), 4);
}
