var map;

function init_map() {
    map = new OpenLayers.Map({
        div: "map",
        projection: "EPSG:900913",
        displayProjection: "EPSG:4326",
        numZoomLevels: 18
    });
    map.addControl(new OpenLayers.Control.LayerSwitcher());

    //var osm = new OpenLayers.Layer.OSM("Open Street Map"); 
    //"http://acetate.geoiq.com/tiles/acetate/${z}/${x}/${y}.png");
 
    var osm = new OpenLayers.Layer.Google(
        "Google Physical",
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
        })
    });

    // allow testing of specific renderers via "?renderer=Canvas", etc
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
    var vectors = new OpenLayers.Layer.Vector("Vector Layer", {
        styleMap: myStyles,
        renderers: renderer
    });
    function update_counter(vl) {
        var area = 0;
        for (i in vl.selectedFeatures) {
            sf = vl.selectedFeatures[i];
            area += sf.data.area;
        }
        $('area').innerHTML = area / 2589988.11; // convert to sq mi 
        $('counter').innerHTML = vl.selectedFeatures.length;
    };

    vectors.events.on({
        'featureselected': function(feature) {
            update_counter(this);
        },
        'featureunselected': function(feature) {
            update_counter(this);
        }
    });

    var url = "/seak/planning_units.geojson";

    OpenLayers.loadURL(url, {}, null, function (response) {
        var gformat = new OpenLayers.Format.GeoJSON();
        var feats = gformat.read(response.responseText);
        vectors.addFeatures(feats);
    });

    map.addLayers([osm, vectors]);
    
    drawControls = {
        select: new OpenLayers.Control.SelectFeature(
            vectors,
            {
                clickout: true, 
                toggle: false,
                multiple: true, 
                hover: false,
                toggleKey: "ctrlKey", // ctrl key removes from selection
                multipleKey: "shiftKey", // shift key adds to selection
                box: true
            }
        ),
    };
    
    for(var key in drawControls) {
        map.addControl(drawControls[key]);
    }
    map.setCenter(new OpenLayers.LonLat(-13600000, 6700000), 4);
}
