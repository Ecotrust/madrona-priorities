var	w = 925,
	h = 550,
	margin = 60,
    startTarget = 0, 
    endTarget = 110,
    /*
    // For objective function score
    startScore = 40,
    endScore = 142,
    */
    startScore = 0,
    endScore = 60,
    y = d3.scale.linear().domain([endScore, startScore]).range([10, h-margin]),
    x = d3.scale.linear().domain([startTarget, endTarget]).range([0 + margin -5, w]),
    targets = d3.range(startTarget, endTarget, 10);

var vis = d3.select("#vis")
    .append("svg:svg")
    .attr("width", w)
    .attr("height", h)
    .append("svg:g")
            
var line = d3.svg.line()
    .x(function(d,i) { return x(d.x); })
    .y(function(d) { return y(d.y); })
    .interpolate('basis');
                    
function containsObject(obj, list) {
    var i;
    for (i = 0; i < list.length; i++) {
        if (list[i] === obj) {
            return true;
        }
    }
    return false;
}

function slugify(str) {
    return str
        .toLowerCase()
        .replace(/ /g,'-')
        .replace(/[^\w-]+/g,'');
}

function getLine(interpolation) {
    return d3.svg.line().x(function(d,i) {
        return x(i)
    }).y(function(d) {
        return y(d)
    }).interpolate(interpolation)
//.tension(0)
}


// Use with objective function score
//d3.text('single_objscore_nocost.csv', 'text/csv', function(text) {
d3.text('single_nocost.csv', 'text/csv', function(text) {
    var speciesCurves = d3.csv.parseRows(text);
    
    categories = [];
    for (i=1; i < speciesCurves.length; i++) {
        // First two cols are non-numeric
        var species = speciesCurves[i][0];
        var category = speciesCurves[i][1];
        if (!containsObject(category, categories)) {
           categories.push(category);
        }
        var values = speciesCurves[i].slice(1, speciesCurves[i.length-1]);
        var currData = [];
        for (j=0; j < values.length; j++) {
            if (j==0) {
                // y starts at 142 for objective function score
                currData.push({ x: 0, y: 0, species: species, category: category });
                continue;
            }
            if (values[j] != '') {
                currData.push({ x: targets[j], y: values[j]});
            }
        }
        vis.append("svg:path")
            .data([currData])
            .attr("species", species)
            .attr("class", slugify(category))
            .attr("d", line)
            .on("mouseover", onmouseover)
            .on("mouseout", onmouseout);
    }
    for (var c=0; c < categories.length; c++) {
        var cat = categories[c];
        html = '<a id="' + slugify(cat) + '">' + cat + '</a>';
        $("#filters").append(html);
    }
    $('#filters a').click(function() {
        var categoryId = $(this).attr("id");
        $(this).toggleClass(categoryId);
        showCategory(categoryId);
    });
});  
    

vis.append("svg:line")
    .attr("x1", x(startTarget))
    .attr("y1", y(startScore))
    .attr("x2", x(endTarget))
    .attr("y2", y(startScore))
    .attr("class", "axis")

vis.append("svg:line")
    .attr("x1", x(startTarget))
    .attr("y1", y(startScore))
    .attr("x2", x(startTarget))
    .attr("y2", y(endScore))
    .attr("class", "axis")
            
vis.append("svg:text")
    .attr("class", "x label")
    .attr("text-anchor", "end")
    .attr("x", w/2.0 + 100)
    .attr("y", h - 6)
    .text("Single species target proportion ");

vis.append("svg:text")
    .attr("class", "y label")
    .attr("text-anchor", "end")
    .attr("y", 1)
    .attr("x", -60)
    .attr("transform", "rotate(-90)")
    .text("Total number of species represented")
    .attr("dy", ".75em");

vis.selectAll(".xLabel")
    .data(x.ticks(5))
    .enter().append("svg:text")
    .attr("class", "xLabel")
    .text(String)
    .attr("x", function(d) { return x(d) })
    .attr("y", h-40)
    .attr("text-anchor", "middle")

vis.selectAll(".yLabel")
    .data(y.ticks(4))
    .enter().append("svg:text")
    .attr("class", "yLabel")
    .text(String)
    .attr("x", 30)
    .attr("y", function(d) { return y(d) })
    .attr("text-anchor", "right")
    .attr("dy", 3)
            
vis.selectAll(".xTicks")
    .data(x.ticks(5))
    .enter().append("svg:line")
    .attr("class", "xTicks")
    .attr("x1", function(d) { return x(d); })
    .attr("y1", y(startScore))
    .attr("x2", function(d) { return x(d); })
    .attr("y2", y(startScore)+7)
    
vis.selectAll(".yTicks")
    .data(y.ticks(12))
    .enter().append("svg:line")
    .attr("class", "yTicks")
    .attr("y1", function(d) { return y(d); })
    .attr("x1", x(startTarget - 0.5))
    .attr("y2", function(d) { return y(d); })
    .attr("x2", x(startTarget))

function onmouseover(d, i) {
    species = d[0]['species'];
    var currClass = d3.select(this).attr("class");
    d3.select(this)
        .attr("class", currClass + " current");
 
    var blurb = '<p style="font-size:12pt;" class="text-success">' + species + '</p>';
    $("#default-blurb").empty();
    $("#default-blurb").hide();
    $("#blurb-content").html(blurb);
}

function onmouseout(d, i) {
    var currClass = d3.select(this).attr("class");
    var prevClass = currClass.substring(0, currClass.length-8);
    d3.select(this)
        .attr("class", prevClass);
    $("#default-blurb").show();
    $("#blurb-content").html('');
}

function showCategory(category) {
    var species = d3.selectAll("path."+category);
    if (species.classed('highlight')) {
        species.attr("class", category);
    } else {
        species.classed('highlight', true);
    }
}

function showFilter(filterText) {
    var species = d3.selectAll("path")
    species.classed('highlight', false);

    if (!filterText || filterText == '')  {
        return;
    } else {
        filterText = filterText.toLowerCase();
        species = d3.selectAll("path").filter(function(d, i) { 
            if (d[0].category && d[0].species)  {
                c = d[0].category.toLowerCase();
                s = d[0].species.toLowerCase();
                return s.indexOf(filterText) !== -1 || c.indexOf(filterText) !== -1;
            }
            return false;
        });
    }
    species.classed('highlight', true);
}

$("input[type='text']#text-filter").bind("change blur keyup", function() {
  showFilter($(this).val());
});