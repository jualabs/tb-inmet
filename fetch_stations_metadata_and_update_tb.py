#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import requests
import yaml
import ast

# load configurations from YAML config file
with open("config.yaml", 'r') as yamlfile:
    cfg_params = yaml.full_load(yamlfile)

TB_HOST = cfg_params['tb_api_access']['host']
token = ''
refresh_token = ''

def rest_result_handler(result):
    # verify if it is a authentication error
    if (result.status_code != 200):
        content = json.loads(result.content)
        print (str(content['status']) + ' : ' + content['message'])

def get_token():
    token_header = {}
    # if token global variable is blank we are not logged in
    if not token:
        print('you are not logged in. call login() first.')
    # return current token
    else:
        token_header['X-Authorization'] = 'Bearer ' + token
        token_header['Content-Type'] = 'application/json'
        token_header['Accept'] = 'application/json'
        
    return token_header

def get_new_token():
    global token
    global refresh_token
    url = 'http://' + TB_HOST + '/api/auth/token'

    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    json_body = {}
    json_body['refreshToken'] = refresh_token
    try:
        result = requests.post(url, headers=headers, json=json_body)
        rest_result_handler(result)
    except ConnectionError:
        print('connection problem on: get_new_token()')
    
    result_json = json.loads(result.content)
    
    try:
        token = result_json['token']
        refresh_token = result_json['refreshToken']
    except KeyError:
        print('unable to get token!')

    return get_token()

def login():
    global token
    global refresh_token
    url = 'http://' + TB_HOST + '/api/auth/login'

    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    json_body = {}
    json_body['username'] = cfg_params['tb_api_access']['user']
    json_body['password'] = cfg_params['tb_api_access']['passwd']
    
    try:
        result = requests.post(url, headers=headers, json=json_body)
        rest_result_handler(result)
    except ConnectionError:
        print('connection problem on: login()')
    
    result_json = json.loads(result.content)
    try:
        token = result_json['token']
        refresh_token = result_json['refreshToken']
    except KeyError:
        print('unable to get token!')

def get_inmet_stations_metadata(cfg_params):
    stations_metadata = []
    # get INMET html station data
    site = cfg_params['inmet_info']['metadata_source_url']
    r = requests.get(site)

    # parse html data
    for l in r.iter_lines(decode_unicode=True):
        line = l.lstrip(" ")
        if 'ESTA' in l:
            parts = line.split(" ")
            metadata = {
                'stationName': '',
                'stationCode': parts[2],
                'latitude': 0,
                'longitude': 0,
                'altitude': 0,
                'launchDate': '',
                'url': '',
                'stationState': '',
                'ommCode':'',
                'mostRecentData':''
            }
            continue
        if 'var html' in line:
            data = line.split('<br>')
            for d in data:
                try:
                    if d[0:3] == '<ta':
                        metadata['url'] = d.split('<a href=')[1].split(" ")[0]
                    elif d[0:3] == '</a':
                        metadata['url'] = d.split('<a href=')[1].split(" ")[0]
                    elif d[0:3] == 'Lat':
                        metadata['latitude'] = d.split(" ")[1][:-1]
                    elif d[0:3] == 'Lon':
                        metadata['longitude'] = d.split(" ")[1][:-1]
                    elif d[0:3] == 'Alt':
                        metadata['altitude'] = d.split(':')[1].replace(" ", "").split("metros")[0]
                    elif d[0:2] == 'Gr':
                        metadata['launchDate'] = d.split('Aberta em:')[1].replace(" ", "").split("<br>")[0]
                    elif 'OMM:' in d:
                        metadata['ommCode'] = d.split(' ')[-1]
                    else:
                        continue
                except Exception as e:
                    print(str(d))
                    print(str(e))
                    continue
        if 'var label' in line:
            parts = line.lstrip("var label =").strip(';').strip('\'')
            parts = l.lstrip(" ").lstrip("var label = ").replace(";", "").replace("\n", "").replace("\'", "").replace(
                " - ", ",").split(",")
            metadata['stationState'] = parts[0]
            metadata['stationName'] = parts[1]
            stations_metadata.append(metadata)
            continue
    return stations_metadata

# entity_type refers to ASSET or DEVICE and type the asset type or device type
def create_entity(name, entity_type='DEVICE', type='AUTOMATIC-STATION'):
    entity_id = ''
    if (entity_type == 'DEVICE'):
        url = 'http://' + TB_HOST + '/api/device'
    elif (entity_type == 'ASSET'):
        url = 'http://' + TB_HOST + '/api/asset'
    else: 
        print('invalid entity type.')
        return

    json_body = {}
    json_body['name'] = name
    json_body['type'] = type

    try:
        result = requests.post(url, json=json_body, headers=get_token())
        rest_result_handler(result)
        # verify if it is an expired token error
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.post(url, json=json_body, headers=get_new_token())
        # in the case that there are no errors
        if (result.status_code == 200):
            result_json = json.loads(result.content)
            entity_id = result_json['id']['id']
        
    except ConnectionError:
        print('connection problem on: create_entity()') 

    result_json = json.loads(result.content)
    
    return entity_id

def create_relation(from_id, from_type, to_id, to_type, relation_type='Contains'):
    url = 'http://' + TB_HOST + '/api/relation'

    json_body = {'from': {'entityType': from_type, 'id': from_id},
                 'to':   {'entityType': to_type, 'id': to_id},
                 'type': relation_type}
    result = {}

    try:
        result = requests.post(url, json=json_body, headers=get_token())
        rest_result_handler(result)
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.post(url, json=json_body, headers=get_new_token())
    except ConnectionError:
        print('connection problem on: create_relation()') 
    
    return result.status_code

def get_all_entities_from_type(entity_type):
    result = {}
    # try to get the asset id by name, if not find it returns an empty string
    # TODO: change the fixed limit
    if (entity_type == 'DEVICE'):
        url = 'http://' + TB_HOST + '/api/tenant/devices?limit=1000'
    elif (entity_type == 'ASSET'):
        url = 'http://' + TB_HOST + '/api/tenant/assets?limit=1000'
    else: 
        print('invalid entity type.')
        return
    
    try:
        result = requests.get(url, headers=get_token())
        rest_result_handler(result)
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.get(url, headers=get_new_token())
    except  ConnectionError:
        print('connection problem on: get_all_entities_from_type()') 
    
    result = json.loads(result.content)

    try:
        result = result['data']
    except  KeyError:
        print('no entities from type ' + entity_type +  ' available.')
        result = []
        pass 

    return result

def delete_entity(entity_id, entity_type='DEVICE'):
    if (entity_type == 'DEVICE'):
        url = 'http://' + TB_HOST + '/api/device/' + entity_id
    elif (entity_type == 'ASSET'):
        url = 'http://' + TB_HOST + '/api/asset/' + entity_id
    else: 
        print('invalid entity type.')
        return

    result = {}
    
    try:
        result = requests.delete(url, headers=get_token())
        rest_result_handler(result)
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.delete(url, headers=get_new_token())
    except ConnectionError:
        print('connection problem on: delete_entity()') 
    
    return result.status_code

def delete_all_entities_from_type(entity_type='DEVICE'):
    all_entities = get_all_entities_from_type(entity_type=entity_type)

    for entity in all_entities:
        delete_entity(entity_id=entity['id']['id'], entity_type=entity_type)

def get_inmet_root_asset_id():
    root_asset_id = get_asset_id('INMET')
    # if there is no root INMET asset, create it, regions, states and relations
    if root_asset_id == '':
        states_on_regions = {'NORTH':['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
                             'NORTHEAST':['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
                             'SOUTH':['PR', 'RS', 'SC'],
                             'SOUTHEAST':['ES', 'MG', 'RJ', 'SP'],
                             'MIDWEST':['DF', 'GO', 'MT', 'MS'],
                             'SPECIALS':[]}
        # create INMET root asset
        root_asset_id = create_entity(name='INMET', entity_type='ASSET', type='INSTITUTION')
        # create REGION and STATES and relations to their REGIONS and INMET
        for region_name, states in states_on_regions.items():
            region_id = create_entity(name=region_name, entity_type='ASSET', type='REGION')
            create_relation(root_asset_id, 'ASSET', region_id, 'ASSET')
            for state_name in states:
                state_id = create_entity(name=state_name, entity_type='ASSET', type='STATE')
                create_relation(region_id, 'ASSET', state_id, 'ASSET')


def get_station_access_token(device_id):
    url = 'http://' + TB_HOST + '/api/device/' + device_id + '/credentials'
    
    credentials = ''
    try:
        result = requests.get(url, headers=get_token())
        rest_result_handler(result)
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.get(url, headers=get_new_token())
        result_json = json.loads(result.content)
        credentials = result_json['credentialsId']
    except  ConnectionError:
        print('connection problem on: get_station_access_token()') 
    except KeyError:
        raise Exception(result_json['message'])
    
    return credentials

# def set_station_attributes(device_id, attributes):
#     # TODO: corrigir o scope to use the new API
#     url = 'http://' + TB_HOST + '/api/plugins/telemetry/DEVICE/' + device_id + '/attributes/CLIENT_SCOPE'
    
#     result = ''

#     try:
#         result = requests.post(url, json=attributes, headers=get_token())
#         if (result.status_code == 401 and result.errorCode == 11):
#             result = requests.post(url, json=attributes, headers=get_new_token())
#     except  ConnectionError:
#         print('connection problem on: set_station_attributes()')   
    
#     result_json = json.loads(result.content)

def set_station_attributes(device_token, attributes):
    # TODO: corrigir o scope
    url = 'http://' + TB_HOST + '/api/v1/' + device_token + '/attributes'
    
    result = ''

    try:
        result = requests.post(url, json=attributes, headers=get_token())
        rest_result_handler(result)
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.post(url, json=attributes, headers=get_new_token())
    except  ConnectionError:
        print('connection problem on: set_station_attributes()')   
    
    result_json = json.loads(result.content)

def get_asset_id(asset_name):
    asset_id = ''
    url = 'http://' + TB_HOST + '/api/tenant/assets?assetName=' + asset_name
    
    try:
        result = requests.get(url, headers=get_token())
        rest_result_handler(result)
        if (result.status_code == 401 and result.errorCode == 11):
            result = requests.get(url, headers=get_new_token())
        result_json = json.loads(result.content)
        asset_id = result_json['id']['id']
    except  ConnectionError:
        print('connection problem on: get_asset_id()')   
    except KeyError:
        asset_id = create_entity(name=asset_name, entity_type='ASSET', type='STATE')
        create_relation(get_asset_id('SPECIALS'), from_type='ASSET', to_id=asset_id, to_type='ASSET')
        pass
    
    return asset_id


def main():
    login()
    # get INMET html stations metadata
    stations_metadata = get_inmet_stations_metadata(cfg_params)
    # get INMET root asset
    get_inmet_root_asset_id()
    # get current inmet stations names from TB
    current_stations_in_tb = get_all_entities_from_type('DEVICE')
    # verify whether a new station exists
    new_stations = []
    for station in stations_metadata:
        # if there is a new station loads its metadata in TB
        if station['stationCode'] not in current_stations_in_tb:
            new_stations.append(station)
    # create new stations at TB
    for station in new_stations:
        attributes = ast.literal_eval(json.dumps(station, ensure_ascii=False))
        device_id = create_entity(name=station['stationCode'], entity_type='DEVICE', type='STATION')
        device_token = get_station_access_token(device_id)
        set_station_attributes(device_token, attributes)
        create_relation(from_id=get_asset_id(station['stationState']), from_type='ASSET', to_id=device_id, to_type='DEVICE')
    
    # delete_all_entities_from_type('ASSET')
    # delete_all_entities_from_type('DEVICE')

if __name__ == '__main__':
    main()

