from datetime import datetime
import googlemaps
from googlemaps import Client as GoogleMaps
from api_key import API_KEY
import requests
import json
import pandas as pd

global api_key
api_key = API_KEY

global county_data
county_data = pd.read_csv("CountyData.csv")

global city_data
city_data = pd.read_csv("Cities_Counties.csv")

global area_data
area_data = pd.read_csv("County_Area.csv")


def generateMap(address):
    # "3749 Armour Court, Fremont, CA 94555 USA"
    # input type, connect gmaps py to html and call function while giving input for address, making input for google maps on page
    gmaps = googlemaps.Client(key=api_key)
    # example address = "6392 Truckee Court, Newark, CA"
    now = datetime.now()

    clipped_address = address.replace(",", "")
    clipped_address = clipped_address.split(" ")
    clipped_address = clipped_address[:5]
    clipped_address = " ".join(str(i) for i in clipped_address)

    directions_result1 = gmaps.directions(clipped_address, "fire station near " + clipped_address,
                                          mode="driving",
                                          departure_time=now)
    directions_result2 = gmaps.directions(clipped_address, "hospital near " + clipped_address,
                                          mode="driving",
                                          departure_time=now)

    timeString1 = directions_result1[0]['legs'][0]['duration']['text']
    timeString2 = directions_result2[0]['legs'][0]['duration']['text']

    time1 = int(timeString1.split()[0])
    time2 = int(timeString2.split()[0])

    if time1 < time2:
        time = timeString1
        distance = directions_result1[0]['legs'][0]['distance']['text']
        destination_address = directions_result1[0]['legs'][0]['end_address']
    else:
        time = timeString2
        distance = directions_result2[0]['legs'][0]['distance']['text']
        destination_address = directions_result2[0]['legs'][0]['end_address']

    print("Destination:", destination_address)
    print("Address:", address)

    destination = destination_address.replace(",", "")
    destination = destination_address.split(" ")

    address = address.replace(",", "")
    address = address.split(" ")

    src = "https://www.google.com/maps/embed/v1/directions?key=" + api_key + "&origin=" + str(destination[0]) + "%20" + \
          str(destination[1]) + "%20" + str(destination[2]) + "%2C%20" + str(destination[3]) + "%2C%20" + \
          str(destination[4]) + "%20" + str(destination[5]) + "%2C%20" + str(destination[6]) + "&destination=" + str(
        address[0]) + "%20" + str(address[1]) + "%20" + str(address[2]) + "%2C%20" + str(address[3]) + "%2C%20" + str(
        address[4]) + "%20" + str(address[5]) + "%2C%20" + str(address[6]) + "&mode=driving&maptype=roadmap"

    return src, time, distance, destination_address


# print(generateMap("3749 Armour Court, Fremont, CA 94555 USA"))


def time_estimate(address="6392 Truckee Court, Newark, CA"):
    gmaps = googlemaps.Client(key=API_KEY)

    now = datetime.now()
    directions_result1 = gmaps.directions(address, "fire station near " + address,
                                          mode="driving",
                                          departure_time=now)
    directions_result2 = gmaps.directions(address, "hospital near " + address,
                                          mode="driving",
                                          departure_time=now)

    timeString1 = directions_result1[0]['legs'][0]['duration']['text']
    timeString2 = directions_result2[0]['legs'][0]['duration']['text']

    time1 = int(timeString1.split()[0])
    time2 = int(timeString2.split()[0])

    if time1 < time2:
        time = timeString1
        distance = directions_result1[0]['legs'][0]['distance']['text']
        destination_address = directions_result1[0]['legs'][0]['end_address']
    else:
        time = timeString2
        distance = directions_result1[0]['legs'][0]['distance']['text']
        destination_address = directions_result1[0]['legs'][0]['end_address']
    return time, destination_address, distance


def getCounty(zip):
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + str(zip) + "&key=" + api_key
    response = requests.get(url)
    response = response.json()
    return str(response["results"][0]["address_components"][2]["long_name"])


def getCountyPop(county):
    countyData = county_data[["COUNTYNAME", "POPULATION"]]
    countyData = countyData.to_dict()
    countyNames = countyData["COUNTYNAME"]
    popData = countyData["POPULATION"]

    inv_countyData = {v: k for k, v in countyNames.items()}
    index = inv_countyData[county]
    return popData[index]


def getUrbanValue(population):
    if population > 50000:
        return 1
    return 0.5


def flatten(t):
    return [item for sublist in t for item in sublist]


def getCitiesInCounty(county):
    if "County" in county:
        county = county.replace(" County", "")
    elif "county" in county:
        county = county.replace(" county", "")

    counties = city_data[city_data["county_name"] == county]
    cities = flatten(counties[["city"]].values.tolist())

    return cities


def getAreaOfCounty(county, state):
    if "County" in county:
        county = county.replace(" County", "")
    elif "county" in county:
        county = county.replace(" county", "")
    countyName = county + ", " + state.upper()
    countyData = area_data[["COUNTY", "AREA"]].to_dict()

    county_names = countyData["COUNTY"]
    county_area = countyData["AREA"]

    county_names = {v: k for k, v in county_names.items()}
    index = county_names[countyName]

    return county_area[index]


'''
Reference"
    <iframe width="600" height="450" style="border:0" loading="lazy" src="https://www.google.com/maps/embed/v1/directions?key={}&origin=5001%20Deep%20Creek%2C%20Rd,%2C%20Fremont,%20CA%2C%2094555,&destination=5121%20Stagecoach%20Street%2C%20Fremont%2C%20CA%2094555%2C%20US&mode=driving&maptype=roadmap"></iframe>.format(API_KEY)
'''


def generateCountyMap(address, stations, hospitals, stationNames, hospitalNames):
    gmaps = GoogleMaps(api_key)

    emergency_locations = stations + hospitals
    emergency_names = stationNames + hospitalNames
    locations = {}

    for x in range(len(emergency_names) - 1):
        # format: {location: [lat, long]}
        locations[emergency_names[x]] = [0, 0]

    for i in range(len(emergency_locations) - 1):
        try:
            geocode_result = gmaps.geocode(emergency_locations[i])
            lat = geocode_result[0]['geometry']['location']['lat']
            long = geocode_result[0]['geometry']['location']['lng']
            locations[emergency_names[i]] = [lat, long]
            # print(locations[emergency_locations[i]])
        except IndexError:
            print("Address was incorrect...")
        except Exception as e:
            print("Unexpected error ocurred.", e)

    src = "https://www.google.com/maps/embed/v1/place?key=" + str(api_key) + "&q=" + str(address)

    return src, locations
