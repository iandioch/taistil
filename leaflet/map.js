function loadJSON(url, callback) {
    request = new XMLHttpRequest;
    request.open('GET', url, true);
    request.onload = function() {
      if (request.status >= 200 && request.status < 400){
        // Success!
        data = JSON.parse(request.responseText);
        callback(data);
      } else {
        console.log("Status code error: " + request.status);
      }
    };

    request.onerror = function() {
      console.log("Error connecting."); 
    };

    request.send();
}

function loadData(callback) {
    console.log("Loading data.");
    loadJSON("http://localhost:1916/api/travel_map", function(data) {
        callback(data);
    });
}

function createMap(callback) {
    loadJSON('http://localhost:1916/api/get_mapbox_token', function(data) {
        console.log("Loading");
        var mapObj = L.map('travel-map').setView([0, -0.09], 1);
        //var accessToken = 'pk.eyJ1IjoiaWFuZGlvY2giLCJhIjoiY2p2ZTlmdGxwMGwzNDQ0bzZ5MWZqcWM4bCJ9.Wj9xHhB0auJ-HqboMXARQw';
        var accessToken = data['token']
        L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + accessToken, {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery &copy; <a href="https://www.mapbox.com/">Mapbox</a>',
            maxZoom: 18,
            id: 'mapbox.light',
            accessToken: accessToken 
        }).addTo(mapObj);
        callback(mapObj);
    });
}

function addDataToMap(mapObj, callback) {
    loadData(function(data) {
        // Add the data.
        console.log("Adding data to map.");
        console.log(data);
        for (i in data.legs) {
            var leg = data.legs[i];
            var points = [
                [leg.dep.lat, leg.dep.lng],
                [leg.arr.lat, leg.arr.lng]
            ];
            var opts = {};
            if (leg.mode === 'AEROPLANE') {
                opts.color = '#4696F0';
                opts.opacity = 0.4;
                var geodesicPoints = [[
                    new L.LatLng(points[0][0], points[0][1]),
                    new L.LatLng(points[1][0], points[1][1])
                ]]
                var line = L.geodesic(geodesicPoints, opts).addTo(mapObj);
                continue;
            } else if (leg.mode === 'BUS') {
                opts.color = '#10634f';
                opts.opacity = 0.6;
            } else if (leg.mode === 'TRAIN') {
                opts.color = '#598e2f';
                opts.opacity = 0.5;
            } else if (leg.mode === 'FILL') {
                opts.color = 'white';
                opts.opacity = 0.5;
            } else {
                opts.color = '#cc3420';
                opts.opacity = 0.7;
            }
            var line = L.polyline(points, opts).addTo(mapObj);
        }
        for (v in data.visits) {
            var loc = data.visits[v].location;
            var lat = loc.lat;
            var lng = loc.lng;
            var num_visits = data.visits[v].num_visits;
            console.log(lat + ", " + lng);
            //var marker = L.marker([lat, lng]).addTo(mapObj);
            var marker = L.circleMarker([lat, lng], {
                'color': 'white',
                'fillColor': '#A00',
                'fillOpacity': 0.9,
                'radius': 5,
                'weight': 1,
            }).addTo(mapObj);
            marker.bindPopup(loc.name + " (" + loc.type + ")<br />Number of visits: " + num_visits);
        }
        callback(mapObj, data);
    });
}

(function() {
    console.log("JS grabbed.");
    createMap(function(map) { addDataToMap(map, function(){}); });
})();
