import sys
# sys.path.append('home/ubuntu/EECS6895')
import os.path
from os import path
from flask import Flask, request, render_template, session, redirect
from flask import flash
from uuid import uuid4
import boto3
import folium
import datetime
import pandas as pd
import json
import branca.colormap as cm

import Manhattan_graph
import Get_traffic_info
import map_center

app = Flask(__name__)
app.secret_key = str(uuid4())

db = boto3.resource('dynamodb')
carsTable = db.Table("Cars")

valid_zones = [4, 12, 13, 24, 41, 42, 43, 45, 48, 50,
               68, 74, 75, 79, 87, 88, 90, 100, 107, 113,
               114, 116, 120, 125, 127, 128, 137, 140, 141, 142,
               143, 144, 148, 151, 152, 153, 158, 161, 162, 163,
               164, 166, 170, 186, 194, 202, 209, 211, 224, 229,
               230, 231, 232, 233, 234, 236, 237, 238, 239, 243,
               244, 246, 249, 261, 262, 263]

gas_zones = [42, 50, 68, 74, 75, 116, 127, 152, 166, 224, 
             238, 243, 244, 249, 263]

Manhattan_map = folium.Map() 
input_date = input_time = ' ' 

def get_geo():
    
    with open('NYC_Taxi_Zones.geojson') as data:
        NYC_geo = json.load(data)
        
    temp = []
    for x in NYC_geo['features']:
        if x['properties']['borough'] == 'Manhattan' and x['properties']['location_id'] != '103':
            temp.append(x)

    Manhattan_geo = NYC_geo.copy()
    Manhattan_geo.update({'features': temp})
    
    return Manhattan_geo

def get_map(Manhattan_geo, points, input_date, input_time, carId, fuel_low, vehicleType):
    # global Manhattan_map, input_date, input_time
    print('get_map', input_date, input_time)
    
    latitude = 40.78
    longitude = -73.96
    
    traffic_info = Get_traffic_info.get_traffic(input_date, input_time) # df
    congestion_info = Get_traffic_info.get_conges(traffic_info) # dict
    
    for z in valid_zones:
        if str(z) not in congestion_info.keys():
            congestion_info[str(z)] = 1
    
    temp = []
    for x in Manhattan_geo['features']:
        zoneID = str(x['properties']['location_id'])
        if congestion_info[zoneID] < 0.85:
            x['properties']['congestion_lv'] = 0
        elif congestion_info[zoneID] >= 0.85 and congestion_info[zoneID] < 1:
            x['properties']['congestion_lv'] = 1
        elif congestion_info[zoneID] >= 1 and congestion_info[zoneID] < 1.25:
            x['properties']['congestion_lv'] = 2
        elif congestion_info[zoneID] >= 1.25 and congestion_info[zoneID] < 1.5:
            x['properties']['congestion_lv'] = 3
        elif congestion_info[zoneID] >= 1.5 and congestion_info[zoneID] < 2:
            x['properties']['congestion_lv'] = 4
        elif congestion_info[zoneID] >= 2:
            x['properties']['congestion_lv'] = 5
        temp.append(x)

    # for y in temp:
    #     try:
    #         print(y['properties']['location_id'], "--", y['properties']['congestion_lv'])
    #     except:
    #         print('error: ', y['properties']['location_id'])
    #         print(congestion_info)
    # Manhattan_geo.update({'features': temp})
    
    # html color string: #008000 : green
    #                    #008B8B : dark cyan
    #                    #0000FF : blue
    #                    #663399 : rebecca purple
    #                    #800080 : purple
    #                    #FF0000 : red
    colormap = cm.LinearColormap(colors = ['#008000', '#008B8B', '#0000FF', '#663399', '#800080', '#FF0000'], 
                                 index=[0, 1, 2, 3, 4, 5])
    
    Manhattan_map = folium.Map(location=[latitude, longitude], zoom_start=12)
    folium.GeoJson(
        Manhattan_geo,
        style_function = lambda feature: {
            'fillColor': colormap(feature['properties']['congestion_lv']),
            'color': 'black',
            'fill_opacity': 1,
            'weight': 2,
            'dashArray': '5, 5'
        }
    ).add_to(Manhattan_map)

    if fuel_low:
        gas = map_center.get_polyline(gas_zones)
        for g in gas:
            folium.Marker(g, icon=folium.Icon(icon='car', prefix='fa')).add_to(Manhattan_map)

    if vehicleType == 'taxi':
        df = pd.read_excel('time_fare.xlsx')
        # print("here", input_time[0:2])
        lucky_zones = list(df[df['time'] == int(input_time[0:2])]['zone'])
        lucky = map_center.get_polyline(lucky_zones)
        for l in lucky:
            folium.Marker(l, icon=folium.Icon(icon='money', prefix='fa')).add_to(Manhattan_map)
    
    if points:
        folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(Manhattan_map)

    Manhattan_map.save('templates/maps/map'+carId+'.html')
    # Manhattan_map.save('templates/map.html')

def createNewCar(driver, carId):

    r = carsTable.put_item(
        Item={
            "CarId"  : carId,
            "Driver" : driver
        }
    )
    return r
    
@app.route('/')
@app.route('/index', methods = ["GET", "POST"])
def index():

    if session == {} or session.get("username", None) == None:
        form = request.form
        if form:
            formInput = form["username"]
            if formInput and formInput.strip():
                session["username"] = request.form["username"]
                print(session["username"])
            else:
                session["username"] = None
        else:
            session["username"] = None

    if request.method == "POST":
        return redirect('/index')

    return render_template("index.html",
                           user=session["username"],
                           carId=session["username"])

@app.route('/logout')
def logout():
    session["username"] = None
    return redirect("/index")

@app.route('/create')
def create():

    if session.get("username", None) == None:

        flash("Need to login to start navigation")
        return redirect("/index")

    else:
        
        driver = session["username"]
        carId = str(uuid4())

        if createNewCar(driver, carId):
            return redirect("/navigate="+carId)

@app.route('/navigate=<carId>')
def navigate(carId):

    if not path.exists('templates/maps/map'+carId+'.html'):
        Manhattan_geo = get_geo()
        get_map(Manhattan_geo, [], '2019-01-01', '00:00', carId, False, 'regularVehicle')

    return render_template("navigate.html",
                        carId=carId,
                        user=session["username"])

@app.route('/route=<carId>', methods=["POST"])
def route(carId):

    form = request.form
    
    input_date = form['inputDate']
    input_time = form['inputTime']
    fuelLv = form['fuelLevel']
    try:
        vehicleType = form['vehicleType']
    except:
        vehicleType = "regularVehicle"

    try:
        src = form['src']
        dest = form['dest']

        carsTable.update_item(
            Key={
                'CarId': carId
            },
            UpdateExpression="SET Src=:s, Dest=:d, FuelLevel=:f, VehicleType=:v",
            ExpressionAttributeValues={
                ':s': src,
                ':d': dest,
                ':f': fuelLv,
                ':v': vehicleType
            }
        )

        graph = Manhattan_graph.graph_init()

        if float(fuelLv) >= 0.25:
            time, route, path = Manhattan_graph.get_path(graph, int(src), int(dest))
            fuel_low = False
        else:
            time, route, path = Manhattan_graph.get_gas_path(graph, int(src), int(dest))
            fuel_low = True

        points = map_center.get_polyline(route)

        # let other vehicle avoid special service cars
        if vehicleType == "specialVehicle":

            route = route.split(" ")

            df = pd.read_excel('graph_weight.xlsx')
            temp = []
            for i in range(len(route) - 1):
                temp.append((int(route[i]), int(route[i + 1])))
            # print(temp)
            for r in temp:
                idx = df.loc[(df['puZone'] == r[0]) & (df['doZone'] == r[1])].index[0]
                df.at[idx,'time'] = 100
            df.to_excel('graph_weight.xlsx')


    except:
        print('except')
        points = []
        fuel_low = False

    Manhattan_geo = get_geo()
    get_map(Manhattan_geo, points, input_date, input_time, carId, fuel_low, vehicleType)

    return redirect('/navigate='+carId)

@app.route('/map_ori')
def map_ori():
    return render_template('map.html')

@app.route('/map=<carId>', methods=["GET"])
def map(carId):
    return render_template('maps/map'+carId+'.html')

# @app.route('/route', methods=['POST', 'GET'])
# def route():
#     global Manhattan_map, input_date, input_time

    # src = request.args.get('src')
    # dest = request.args.get('dest')
    # print(src, dest)

    # graph = Manhattan_graph.graph_init()
    # time, route, path = Manhattan_graph.get_path(graph, int(src), int(dest))

    # points = map_center.get_polyline(route)

    # Manhattan_geo = get_geo()
    # get_map(Manhattan_geo, points)

    # return route

if __name__ == '__main__':
    app.run(debug = True)
    # app.run(host="0.0.0.0", port = 5000)
