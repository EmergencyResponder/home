from flask import Flask, render_template, request, redirect, url_for, jsonify
from gmaps import generateMap, getCounty, getCountyPop, getUrbanValue, getAreaOfCounty
from MapStations import stationCalc, hospitalCalc
import FindingStations as fs
from api_key import API_KEY
from model import predict
import googlemaps
import regex as re
import urllib

app = Flask(__name__)
google_maps = googlemaps.Client(key=API_KEY)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        address = request.form['address']
        try:
            pattern = re.compile("[0-9]+ ([a-zA-Z]+ )?([a-zA-Z]+ )?([a-zA-Z]+ )?([a-zA-Z]+ )?[a-zA-Z]+, ([a-zA-Z]+ )?"
                                 "([a-zA-Z]+ )?([a-zA-Z]+ )?([a-zA-Z]+ )?[a-zA-Z]+, ([a-zA-Z]+ )?[a-zA-Z]+ [0-9]+, "
                                 "([a-zA-Z]+ )?[a-zA-Z]+")
            geocode_result = google_maps.geocode(address)
            # print(geocode_result)
            geocode_input = geocode_result[0]['formatted_address']
            if re.search(pattern, geocode_input):
                return redirect(url_for('services', address=geocode_input))
            else:
                error_msg = "Please input a valid address. Example: 6392 Truckee Court, Newark, CA"
        except:
            error_msg = "Please input an address. Example: 6392 Truckee Court, Newark, CA"
        return render_template('index.html', error_msg=error_msg)
    else:
        return render_template('index.html')


@app.route('/about-us', methods=['POST', 'GET'])
def about_us():
    return render_template('elements.html')


@app.route('/services', methods=['POST', 'GET'])
def services():
    time = predicted_county_time = 0
    destination = src = distance = county_src = address = addr_county = "None"
    locations = {}
    map_center = [40.3453453, -79.8327498]
    go_home = False
    hospital_addresses = station_addresses = ['']
    script_src = "https://maps.googleapis.com/maps/api/js?key={}&callback=initialize_map".format(API_KEY)
    if request.method == 'POST':
        latitude = request.get_json()[0]
        longitude = request.get_json()[1]
        address = google_maps.reverse_geocode((latitude, longitude))[0]['formatted_address']
        address = {'address': urllib.parse.urlencode({'address': address})}
        return jsonify(address)
    try:
        address = request.args.get('address')
        address_components = google_maps.geocode(address)

        map_center = [address_components[0]['geometry']['location']['lat'],
                      address_components[0]['geometry']['location']['lng']]

        _, station_addresses, station_names = stationCalc(address)
        _, hospital_addresses, hospital_names = hospitalCalc(address)
        print("did calcs")
        print(station_addresses, hospital_addresses)

        for station in station_addresses:
            station_components = google_maps.geocode(station)
            locations[station] = [station_components[0]['geometry']['location']['lat'],
                                  station_components[0]['geometry']['location']['lng']]

        for hospital in hospital_addresses:
            hospital_components = google_maps.geocode(hospital)
            locations[hospital] = [hospital_components[0]['geometry']['location']['lat'],
                                   hospital_components[0]['geometry']['location']['lng']]
        addr_county = address_components[0]['address_components'][3]['short_name']
        addr_state = address_components[0]['address_components'][4]['short_name']
        print("Got county/state")
        try:

            hospital_num, _, ch = fs.hospitalCalc(addr_county, addr_state)
            station_num, _, cs = fs.stationCalc(addr_county, addr_state)
            prediction_stations = hospital_num + station_num
            print(prediction_stations)

            prediction_area = getAreaOfCounty(addr_county, addr_state)
            print(prediction_area)

            zip_code = address_components[0]['address_components'][6]['long_name']
            prediction_county = getCounty(zip_code)
            prediction_pop = getCountyPop(prediction_county)
            urban_value = getUrbanValue(prediction_pop)
            predicted_county_time = int(predict(prediction_stations, prediction_area, urban_value))
            print(predicted_county_time)
        except:
            print("inner problem")
        src, time, distance, destination = generateMap(address)
        print("Generated map")
    except:
        go_home = True

    markers = []
    for location in locations:
        loc_lat_long = [locations[location][0], locations[location][1], location,
                        '/static/images/marker.png']
        markers.append(loc_lat_long)
    return render_template('landing.html',
                           time=time,
                           address=address,
                           destination=destination,
                           distance=distance,
                           go_home=go_home,
                           src=src,
                           county_src=county_src,
                           map_center=map_center,
                           closest_hospital=hospital_addresses[0],
                           closest_station=station_addresses[0],
                           markers=markers,
                           addr_county=addr_county,
                           predicted_county_time=predicted_county_time,
                           script_src=script_src
                           )


@app.route('/education', methods=['POST', 'GET'])
def education():
    return render_template('generic.html')
