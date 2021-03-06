


//Initialize Map and bind filter button
//TODO:
//Add event handlers for map zoom/move
$(document).ready(function () {
    document.querySelector("google-map").addEventListener('api-load', function(e) {
      map.init();
  });
	$("#tButton").click(function() {
		st = "Thu, 01 Jan 1970 05:00:00 GMT";
		end = "Sat, 01 Jan 2050 05:00:00 GMT";
		radius = 10;
		cost = Number.MAX_VALUE;
		tags = [];

		if($('#startTimePicker').data("DateTimePicker").date() != null) {
		  st = $('#startTimePicker').data("DateTimePicker").date().toDate().toUTCString();
    }

		if($('#endTimePicker').data("DateTimePicker").date() != null) {
		  end = $('#endTimePicker').data("DateTimePicker").date().toDate().toUTCString();
		}

		if( $('#radius').val() != "") {
			radius = $('#radius').val();
		}

		if( $('#cost').val() != "") {
			cost = $('#cost').val();
		}

		temp = $('#tags').val();
		if(temp.length != "") {
  		temp = temp.replace(/ /g,'');
  		temp = temp.toLowerCase();
  		tags = temp.split(',');
		}
		filterBy(st, end, radius, tags, cost);
	})
});


//Map Object to hold map parameters
//and will be used for map event handling
var map = {
  mapElement: null,
  map: null,
  markers: null,
  zoom: null,
  leftBound: null,
  rightBound: null,
  bottomBound: null,
  topBound: null,

  //initialize map properties
  init: function() {
    map.mapElement = document.querySelector("google-map");
    map.map = map.mapElement.map;
    map.zoom = map.map.getZoom();
    map.markers = Array.prototype.slice.call(document.querySelectorAll("google-map-marker"));
  },

  //constructs the marker HTML for an event and adds it to the map
  addMarker: function(ev) {
  	var m = document.createElement('google-map-marker');
    m.id = ev._id;

    m.longitude = ev.location.loc.coordinates[0];
    m.latitude = ev.location.loc.coordinates[1];
    m.title = ev.title;
    var h3 = document.createElement("h3");
    var a = document.createElement("a");
    a.href = "/event/" + ev._id;
    a.innerText = ev.title;
    h3.appendChild(a);
    m.appendChild(h3);
    var p2 = document.createElement("p");

    //TODO:
    //Fix the dates so they are formatted correctly
    var sd  = new Date(ev.start_date.$date);
    var ed = new Date(ev.end_date.$date);
    p2.innerText = sd + " -- " + ed;
    m.appendChild(p2);

    var p3 = document.createElement("p");
    p3.innerText = ev.location.address;
    m.appendChild(p3);
    map.mapElement.appendChild(m);
    map.markers.push(m);
  },

  //following 3 functions are for future implementation with draggable map events
  updateBounds: function() {
    //framework for map movement events
    map.leftBound = map.map.getBounds.getSouthWest().lng();
    map.bottomBound = map.map.getBounds.getSouthWest().lat();
    map.rightBound = map.map.getBounds.getNorthEast().lng();
    map.topBound = map.map.getBounds.getNorthEast().lat();
  },

  move: function() {
    map.updateBounds();
    //future will call filterBy
  },

  click: function() {
    map.updateBounds();
    //future will call filterBy
  }
};

//filters the markers displayed on the map
//currently only by time/radius
function filterBy(startTime, endTime, rad, tags, attCost) {
  //AJAX CALL
  $.getJSON($SCRIPT_ROOT + '/filter', {
    //set fields to send
    start: startTime,
    end: endTime,
    radius: rad,
    cost: attCost,
    tags: JSON.stringify(tags)
  },
  //CALLBACK FUNCTION
  function(data) {
    //remove all markers currently on the map
    //that were not found in the database query
    //by setting their map reference to null
    for(var i = 0; i < map.markers.length; i++) {
      if(isIn(map.markers[i], "id", data, "_id") == null) {
        map.markers[i].marker.setMap(null);
      }
    }

    //for each marker returned by the database query
    for(var i = 0; i < data.length; i++) {
      temp = new Date(data[i].start_date.$date);

      //if the marker is already in map.markers
      //set the markers reference to the map
      temp = isIn(data[i], "_id", map.markers, "id");
      if(temp != null) {
        temp.marker.setMap(map.map);
      }
      //else create a new marker and add it to the map/list of markers
      else {
        map.addMarker(data[i]);
      }
    }
		seperateMarkers();
  });
}

//function to check if and item exists in a list 
//by checking a specific attribute
//called by filterBy()
function isIn(m, mAttr, l, lAttr) {
  for(var i = 0; i < l.length; i++) {
    if(l[i][lAttr].trim() == m[mAttr].trim()) {
      return l[i];
    }
  }
  return null;
}
