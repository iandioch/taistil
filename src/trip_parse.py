import json
import sys
import time

from collections import defaultdict

import requests

from jsonschema import validate

SECONDS_SLEEP_ON_RATE_LIMITING = 4
SECONDS_SLEEP_BETWEEN_REQUESTS = 0.66
ESTIMATED_RATE_LIMIT_TIME_MULTIPLE = 2


'''
Use the Google Maps API to search a given string.

Returns (error, full_address, latitude, longitude, address_components) tuple.
'''
def get_coords_for_location(loc):
    u = 'https://maps.googleapis.com/maps/api/geocode/json?address={}'
    resp = json.loads(requests.get(u.format(loc)).text)
    if resp['status'] != 'OK':
        return resp['status'], None, None, None, None
    for result in resp['results']:
        addr = result['formatted_address']
        lat = float(result['geometry']['location']['lat'])
        lng = float(result['geometry']['location']['lng'])
        components = result['address_components']
        return None, addr, lat, lng, components
    return 'NO_RESULTS', None, None, None, None


'''
Recursively walk through the trip elements and return a set of all locations.
'''
def get_locations(data, queue=set()):
    if 'elements' in data:
        for element in data['elements']:
            get_locations(element)
    else:
        queue.add(data['location'])
    return queue 


'''
Iterate over a list of locations in order and fetch data about each one.

Prints progress reports as it goes.

Waits between requests to reduce load on the Google Maps service, and 
times out for a short time when it hits a rate limit.

Returns a {input_location: location_data_tuple} dict.

If a location cannot be found, it will not appear in the dict as a key.
'''
def get_location_data(locations):
    location_data = {}
    i = 0
    while i < len(locations):
        if i > 0:
            # Reduce the load on the server between requests.
            time.sleep(SECONDS_SLEEP_BETWEEN_REQUESTS)
        error, *data = get_coords_for_location(locations[i])
        progress_str = '({}/{})'.format(i+1, len(locations))
        time_left = (len(locations) - (i+1))*SECONDS_SLEEP_BETWEEN_REQUESTS*ESTIMATED_RATE_LIMIT_TIME_MULTIPLE
        time_left_str = '~{} seconds remaining'.format(int(time_left))
        if not error:
            location_data[locations[i]] = data
            print('Received location data for', locations[i], progress_str, time_left_str, '✔')
            i += 1
            continue
        if error == 'NO_RESULTS':
            print('No location data found for location: ', locations[i], progress_str, '✗')
            i += 1
            continue
        if error == 'OVER_QUERY_LIMIT':
            print('Waiting for rate limiting to subside ⚠')
            time.sleep(SECONDS_SLEEP_ON_RATE_LIMITING)
            continue
        print('Location "', locations[i], '" had error "', error, '". Skipping. ✗')
        i += 1
    return location_data


'''
Given a Taistil element and the loaded location data, output stats
on countries visited.
'''
def get_location_statistics(taistil_data, location_data):
    def get_location_list(data, queue=[]):
        if 'elements' in data:
            for element in data['elements']:
                get_location_list(element)
        else:
            queue.append(data['location'])
        return queue 
    countries = defaultdict(int)
    airports = defaultdict(int)
    cities = defaultdict(int)
    unique_countries = defaultdict(set)
    locations = get_location_list(taistil_data)
    for location in locations:
        if location not in location_data:
            continue
        *_, components = location_data[location]
        for component in components:
            print(component)
            if 'country' in component['types']:
                countries[component['long_name']] += 1
                unique_countries[component['long_name']].add(location)
            elif 'airport' in component['types']:
                airports[component['long_name']] += 1
            elif 'locality' in component['types']:
                cities[component['long_name']] += 1

    def dict_count_to_tuple_list(counts):
        tuples = list(counts.items())
        tuples.sort()
        tuples.sort(key=lambda x:x[1], reverse=True)
        return tuples
    country_tuples = dict_count_to_tuple_list(countries)
    airport_tuples = dict_count_to_tuple_list(airports)
    city_tuples = dict_count_to_tuple_list(cities)
    unique_countries = {k:len(unique_countries[k]) for k in unique_countries}
    unique_country_tuples = dict_count_to_tuple_list(unique_countries)
    return country_tuples, airport_tuples, city_tuples, unique_country_tuples


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Please provide as an argument the location of the trip element json schema')
        print('Provide the document you want to parse as stdin.')
    else:
        schema_file = ' '.join(sys.argv[1:])
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        doc = json.load(sys.stdin)

        validate(doc, schema)
        print('Input conforms to JSON schema ✔')
        locations = list(get_locations(doc))
        location_data = get_location_data(locations)
        print(location_data)
        countries, airports, cities, uniques = get_location_statistics(doc, location_data)
        def print_top_n(title, data, n):
            print('{:<40}{:>10}'.format(title, 'Count'))
            print('-'*50)
            for i in range(n):
                if i >= len(data):
                    break
                print('{:>3}. {:<40} {:>4}'.format(i+1, data[i][0], data[i][1]))
        print_top_n("Countries travelled in", countries, 10)
        print_top_n("Cities travelled in", cities, 10)
        print_top_n("Airports travelled in", airports, 6)
        print_top_n("Unique places visited in countries", uniques, 5)
