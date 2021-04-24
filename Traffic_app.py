import json
import folium
import streamlit as st
from streamlit_folium import folium_static
import datetime
import branca.colormap as cm
import Get_traffic_info

valid_zones = [4, 12, 13, 24, 41, 42, 43, 45, 48, 50,
               68, 74, 75, 79, 87, 88, 90, 100, 107, 113,
               114, 116, 120, 125, 127, 128, 137, 140, 141, 142,
               143, 144, 148, 151, 152, 153, 158, 161, 162, 163,
               164, 166, 170, 186, 194, 202, 209, 211, 224, 229,
               230, 231, 232, 233, 234, 236, 237, 238, 239, 243,
               244, 246, 249, 261, 262, 263]

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

def get_map(Manhattan_geo, input_date, input_time):
    
    latitude = 40.78
    longitude = -73.96
    
    traffic_info = Get_traffic_info.get_traffic(input_date, input_time) # df
    congestion_info = Get_traffic_info.get_conges(traffic_info) # dict
    
    for z in valid_zones:
        if str(z) not in congestion_info.keys():
            congestion_info[str(z)] = 1
            
#     c = list(congestion_info.values())
#     print(congestion_info)
#     for i in valid_zones:
#         print(congestion_info[i])
    
    temp = []
    for x in Manhattan_geo['features']:
        zoneID = str(x['properties']['location_id'])
        if congestion_info[zoneID] < 0.85:
#             print('green')
            x['properties']['congestion_lv'] = 0
        elif congestion_info[zoneID] >= 0.85 and congestion_info[zoneID] < 1.5:
            x['properties']['congestion_lv'] = 1
        elif congestion_info[zoneID] > 1.5:
#             print('red')
            x['properties']['congestion_lv'] = 2
        temp.append(x)
    Manhattan_geo.update({'features': temp})
    

    colormap = cm.LinearColormap(colors = ['green', 'blue', 'red'], index = [0, 1, 2])
    
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
    
    return Manhattan_map
    

def main():
    
    st.title('Smart Traffic System :sunglasses:')
    input_date = st.date_input('Pick a date', value = datetime.datetime(2019, 1, 1),\
                               min_value = datetime.datetime(2019, 1, 1), \
                               max_value = datetime.datetime(2020, 1, 1))
    input_time = st.time_input('Pick a time', value = datetime.time(0, 0))
    Manhattan_geo = get_geo()
    Manhattan_map = get_map(Manhattan_geo, input_date, input_time)
#     Manhattan_map.save('map.html')
    folium_static(Manhattan_map)
    
if __name__ == '__main__':
    main()