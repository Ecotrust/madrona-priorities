$(document).ready(function() {
    init();
});

var map, controls;
var stands;
var currentStep = 1;
var steps = [undefined]; // start with a blank to make it 1-indexed

function init() {
    map = new OpenLayers.Map({
        div: "map",
        projection: "EPSG:900913",
        displayProjection: "EPSG:4326",
        numZoomLevels: 18
    });
    map.addControl(new OpenLayers.Control.LayerSwitcher());
    //map.addControl(new OpenLayers.Control.Zoom());
    var osm = new OpenLayers.Layer.OSM( "Simple OSM Map");
    var myStyles = new OpenLayers.StyleMap({
        "default": new OpenLayers.Style({
            fillColor: "#ffffff",
            fillOpacity: 0.4,
            strokeColor: "#339933",
            strokeWidth: 1,
            graphicZIndex: 1
        }),
        "select": new OpenLayers.Style({
            fillColor: "#ffff00",
            fillOpacity: 0.6,
            graphicZIndex: 2
        })
    });
    

    map.addLayers([osm]);

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

    // new app methods
    app.cleanupForm = function ($form) {
      // remove the submit button, strip out the geometry
      $form
        .find('input:submit').remove().end()
        .find('#id_geometry_final').closest('.field').remove();

      // put the form in a well and focus the first field
      $form.addClass('well');
      $form.find('.field').each(function () {
        var $this = $(this);
        // add the bootstrap classes
        $this.addClass('control-group');
        $this.find('label').addClass('control-label');
        $this.find('input').wrap($('<div/>', { "class": "controls"}));
        $this.find('.controls').append($('<p/>', { "class": "help-block"}));

      });
      $form.find('input:visible').first().focus();
      
    }
}; //end init

