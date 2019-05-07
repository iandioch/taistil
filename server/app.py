import json

from collections import defaultdict

from taisteal_csv import parse
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

with open('config.json') as f:
    config = json.load(f)

@app.route('/')
def serve_root():
    return 'Hello World!'

@app.route('/api/travel_map')
def serve_travel_map():
    def _get_location_dict(loc):
        # Turn a Location object into a json-dumpable form.
        return {
            'lat': loc.latitude,
            'lng': loc.longitude,
            'name': loc.address,
        }

    loc = '../../mo_thaistil/2018_02_20_Lugano.csv'
    loc = '../out.csv'
    travel_leg_series = parse.parse(loc)

    legs = []
    num_visits = defaultdict(int)
    name_to_loc = {}
    for leg in travel_leg_series.legs:
        departure_loc = _get_location_dict(leg.dep.loc)
        arrival_loc = _get_location_dict(leg.arr.loc)
        legs.append({
            'dep': departure_loc,
            'arr': arrival_loc,
            'mode': leg.mode,
        })
        num_visits[departure_loc['name']] += 1
        num_visits[arrival_loc['name']] += 1
        name_to_loc[departure_loc['name']] = departure_loc
        name_to_loc[arrival_loc['name']] = arrival_loc 

    visits = []
    for v in sorted(num_visits, key=lambda x:num_visits[x]):
        visits.append({
            'location': name_to_loc[v],
            'num_visits': num_visits[v],
        })
    data = {
        'legs': legs,
        'visits': visits,
    }
    s = json.dumps(data, indent=4)
    print(s)
    return s

@app.route('/api/get_mapbox_token')
def serve_get_mapbox_token():
    return json.dumps({
        'token': config['mapbox_token']
    })

def main():
    app.run(port=1916)

if __name__ == '__main__':
    main()
