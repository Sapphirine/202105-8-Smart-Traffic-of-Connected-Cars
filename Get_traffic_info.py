import json
import requests
import pandas as pd
import datetime
import Manhattan_graph

def data_process(df):
    
    df_processed = df.copy()
    dropped_col = ['vendorid', 'passenger_count', 'ratecodeid', 'store_and_fwd_flag',
                 'payment_type', 'fare_amount', 'extra', 'mta_tax', 'tip_amount',
                  'tolls_amount', 'improvement_surcharge', 'total_amount', 'payment_type',
                  'trip_type', 'congestion_surcharge']
    
    for x in dropped_col:
        try:
            df_processed = df_processed.drop([x], axis = 1)
        except:
            pass
        
#     make the column names consistent between green and yellow taxi dataset
    df_processed = df_processed.rename(columns = {"tpep_pickup_datetime":"pickup_datetime",
                                                  "tpep_dropoff_datetime": "dropoff_datetime"})
    df_processed = df_processed.rename(columns = {"lpep_pickup_datetime":"pickup_datetime",
                                                  "lpep_dropoff_datetime": "dropoff_datetime"})
    
    return df_processed

def calculate_time(row0, row1):
    t1 = datetime.datetime.strptime(row0, '%Y-%m-%dT%H:%M:%S.000')
    t2 = datetime.datetime.strptime(row1, '%Y-%m-%dT%H:%M:%S.000')
    return round((t2 - t1).seconds / 60, 1)


def get_traffic(input_date, input_time):
    
    url_green = 'https://data.cityofnewyork.us/resource/q5mz-t52e.json'
    url_yellow = 'https://data.cityofnewyork.us/resource/2upf-qytp.json'

    valid_zones = [4, 12, 13, 24, 41, 42, 43, 45, 48, 50,
                   68, 74, 75, 79, 87, 88, 90, 100, 107, 113,
                   114, 116, 120, 125, 127, 128, 137, 140, 141, 142,
                   143, 144, 148, 151, 152, 153, 158, 161, 162, 163,
                   164, 166, 170, 186, 194, 202, 209, 211, 224, 229,
                   230, 231, 232, 233, 234, 236, 237, 238, 239, 243,
                   244, 246, 249, 261, 262, 263]

    parameters_PU = '&$where=(PULocationID=4'
    parameters_DO = '+AND+(DOLocationID=4'
    for zone in valid_zones[1::]:
        parameters_PU += '+OR+PULocationID=' + str(zone)
        parameters_DO += '+OR+DOLocationID=' + str(zone)
    parameters_PU += ')'
    parameters_DO += ')'

    parameters = '?$offset=0&$limit=8000'
    parameters += parameters_PU + parameters_DO
    
    temp = str(input_date) + "T" + str(input_time)
    try:
        t1 = datetime.datetime.strptime(temp, '%Y-%m-%dT%H:%M:%S')
    except:
        t1 = datetime.datetime.strptime(temp, '%Y-%m-%dT%H:%M')
    t2 = t1 + datetime.timedelta(minutes = 15)
    print(t1, t2)

    parameters += '+AND+(tpep_dropoff_datetime+BETWEEN+"{}"+and+"{}")'\
                  .format(t1.isoformat(), t2.isoformat())

    response = requests.get(url_yellow + parameters)
    data = response.json()
    data = pd.DataFrame(data)

    df = data_process(data)
    df['time'] = [calculate_time(row[0], row[1]) \
                  for row in zip(df['pickup_datetime'], df['dropoff_datetime'])]
    
    return df
    
    
def get_conges(df):
    
    g = Manhattan_graph.graph_init()
    conges_level_temp = {}
    
    for row in zip(df['pulocationid'], df['dolocationid'], df['time']):
        
        try:
            t, p = Manhattan_graph.get_path(g, int(row[0]), int(row[1]))
        except:
            t = 7.5 # average time of trip with same starting point and destination
            p = row[1]
            
        for zone in p.split(' '):
            ratio = row[2] / t # needs further research (traffic congestion)
            
            try:
                conges_level_temp[zone].append(ratio)
            except:
                conges_level_temp[zone] = [ratio]
    
    conges_level = {zone: round(sum(ratios) / len(ratios), 2) for zone, ratios in conges_level_temp.items()}
    
    return conges_level

    
    
