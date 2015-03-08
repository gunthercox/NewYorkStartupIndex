from flask import Flask
from pymongo import MongoClient
from flask import jsonify
from bson.json_util import dumps
from flask import request
import json

client = MongoClient()

app = Flask(__name__, static_folder="static", static_url_path="")

def to_geo_json(lat_lon):
    """
    Pass in the lat and lon of a point.
    Returns a mongo geojson point.
    """
    return {
        "loc": {
            "type": "Point",
            "coordinates": lat_lon
        }
    }

def populate():
    """
    Fill the database with wonderfull data
    """
    # Clear the previous collection data
    client.geo['crime'].remove()
    client.geo['business_licenses'].remove()
    client.geo['public_transportation'].remove()

    crime_data_files = [
        "./data/robbery.geojson",
        #"./data/rape.geojson",
        "./data/murder.geojson",
        "./data/grandlarceny.geojson",
        "./data/grandlarcenyofauto.geojson",
        "./data/felonyassault.geojson",
        "./data/burglaries.geojson"
    ]

    public_transportation = [
        "./data/bike-shelters.geojson",
        "./data/busstops.geojson",
        "./data/subways.geojson",
        "./data/khv.geojson"
    ]

    # Load crime data files
    for data_file in crime_data_files:
        crime_data = open(data_file, "r")
        crime_data = json.load(crime_data)["features"]

        data = client.geo['crime']
        data.ensure_index([("geometry", "2dsphere")])
        data.insert(crime_data)

    # Load public transportation data
    for data_file in public_transportation:
        transportation_data = open(data_file, "r")
        transportation_data = json.load(transportation_data)["features"]

        data = client.geo['public_transportation']
        data.ensure_index([("geometry", "2dsphere")])
        data.insert(transportation_data)

    # Load business license data
    license_data = open("./data/competition.geojson", "r")
    license_data = json.load(license_data)["features"]

    data = client.geo['business_licenses']
    data.ensure_index([("geometry", "2dsphere")])
    data.insert(license_data)

populate()


@app.route("/index")
def index():
    from flask import render_template
    return render_template("index.html")


@app.route("/crime")
def crime():
    if "radius" in request.args:

        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        radius = float(request.args["radius"])

        crime = client.geo['crime'].find({
            "geometry": {
                "$geoWithin": {
                    "$centerSphere": [
                        [lat, lon],
                        # Radius in miles
                        radius / 3959.0
                    ]
                }
            }
        })
    else:
        crime = client.geo['crime'].find()

    results = json.loads(dumps(crime))
    return jsonify({
        "type": "FeatureCollection",
        "features": results
    })


@app.route("/business_licenses")
def business_licenses():
    if "radius" in request.args:

        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        radius = float(request.args["radius"])

        crime = client.geo['business_licenses'].find({
            "geometry": {
                "$geoWithin": {
                    "$centerSphere": [
                        [lat, lon],
                        # Radius in miles
                        radius / 3959.0
                    ]
                }
            }
        })
    else:
        crime = client.geo['business_licenses'].find()

    results = json.loads(dumps(crime))
    return jsonify({
        "type": "FeatureCollection",
        "features": results
    })


@app.route("/public_transportation")
def public_transportation():

    types = ["Taxis", "Bus", "Bike", "Subways"]

    if "exclude_type" in request.args:
        arguments = request.args["exclude_type"].split(" ")

        # If all of the request items are in the types list
        for argument in arguments:
            if argument in types:
                types.remove(argument)

    if "radius" in request.args:

        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        radius = float(request.args["radius"])

        transportation = client.geo['public_transportation'].find({
            "geometry": {
                "$geoWithin": {
                    "$centerSphere": [
                        [lat, lon],
                        # Radius in miles
                        radius / 3959.0
                    ]
                }
            }, "properties.type": {
                "$in": types
            }
        })
    else:
        transportation = client.geo['public_transportation'].find()

    results = json.loads(dumps(transportation))
    return jsonify({
        "type": "FeatureCollection",
        "features": results
    })


if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.run(host="0.0.0.0", port=8000)
