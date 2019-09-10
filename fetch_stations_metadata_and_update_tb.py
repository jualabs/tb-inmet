#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import swagger_client
from swagger_client.rest import ApiException
from tb_inmet_utils import renew_token
from tb_inmet_utils import get_tb_api_configuration
import json
import requests
import yaml
import ast

# load configurations from YAML config file
with open("config.yaml", 'r') as yamlfile:
    cfg_params = yaml.load(yamlfile)

TB_HOST = cfg_params['tb_api_access']['host']

# get API access configuration object
configuration = get_tb_api_configuration(cfg_params)

# create instances of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))
asset_controller_api_inst = swagger_client.AssetControllerApi(swagger_client.ApiClient(configuration))
entity_relation_controller_api_inst = swagger_client.EntityRelationControllerApi(swagger_client.ApiClient(configuration))

def get_current_token():
    url = 'http://' + TB_HOST + '/api/auth/login'

    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    values_token = {}
    values_token['username'] = cfg_params['tb_api_access']['user']
    values_token['password'] = cfg_params['tb_api_access']['passwd']
    result = requests.post(url, json=values_token)
    json_message = json.loads(result.content)

    token = {}
    # print 'Bearer ' + json_message['token']
    token['X-Authorization'] = 'Bearer ' + json_message['token']
    token['Content-Type'] = 'application/json'
    token['Accept'] = 'application/json'

    return token

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

def get_asset_id_by_name(name, token):
    asset_id = ''
    # try to get the asset id by name, if not find it returns an empty string
    url = 'http://' + TB_HOST + '/api/tenant/assets?assetName=' + name
    result = requests.get(url, headers=token)
    result = json.loads(result.content)
    try:
        asset_id = result['id']['id']
    except:
        asset_id = ''
        pass
    return asset_id

def create_asset(name, type='STATE'):
    url = 'http://' + TB_HOST + '/api/asset'

    params = {}
    params['name'] = name
    params['type'] = type
    result = requests.post(url, json=params, headers=get_current_token())
    result_json = json.loads(result.content)
    return result_json['id']['id']

def create_relation(relation):
    url = 'http://' + TB_HOST + '/api/relation'
    result = requests.post(url, json=relation, headers=get_current_token())
    return result.status_code


def get_inmet_root_asset_id():
    root_asset_id = get_asset_id_by_name('INMET', get_current_token())
    # if there is no root INMET asset, create it, regions, states and relations
    if root_asset_id == '':
        regions = {'NORTH': 0, 'NORTHEAST': 0, 'SOUTH': 0, 'SOUTHEAST': 0, 'MIDWEST': 0}
        states_on_regions = {'NORTH':{'AC': 0, 'AP': 0, 'AM': 0, 'PA': 0, 'RO': 0, 'RR': 0, 'TO': 0},
                             'NORTHEAST':{'AL': 0, 'BA': 0, 'CE': 0, 'MA': 0, 'PB': 0, 'PE': 0, 'PI': 0, 'RN': 0, 'SE': 0},
                             'SOUTH':{'PR': 0, 'RS': 0, 'SC': 0},
                             'SOUTHEAST':{'ES': 0, 'MG': 0, 'RJ': 0, 'SP': 0},
                             'MIDWEST':{'DF': 0, 'GO': 0, 'MT': 0, 'MS': 0}}
        relation = {'from': {'entityType': 'ASSET', 'id': root_asset_id},
                    'to':   {'entityType': 'ASSET', 'id': ""},
                    'type': 'Contains'}
        # create INMET root asset
        root_asset_id = create_asset('INMET', 'INSTITUTION')
        relation['from']['id'] = root_asset_id
        # create REGIONS and relation to INMET
        for region_name, region_id in regions.items():
            regions[region_name] = create_asset(region_name, 'REGION')
            relation['to']['id'] = regions[region_name]
            create_relation(relation)
        # create STATES and relations to their REGIONS
        for region_name, states in states_on_regions.items():
            relation['from']['id'] = regions[region_name]
            for state_name, state_id in states.items():
                states[state_name] = create_asset(state_name, 'STATE')
                relation['to']['id'] = states[state_name]
                create_relation(relation)

def get_tb_inmet_current_stations(cfg_params):

    relation_search_parameters = swagger_client.RelationsSearchParameters(
        root_id=cfg_params['tb_entities_access']['root_asset_id'], root_type='ASSET', direction='FROM', max_level=0)
    query = swagger_client.DeviceSearchQuery(device_types=['automatic-station'], parameters=relation_search_parameters,
                                             relation_type='Contains')
    query.parameters = relation_search_parameters

    while True:
        try:
            devices_list = device_controller_api_inst.find_by_query_using_post1(query)
            # print(devices_list)
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceControllerApi->find_by_query_using_post1: %s\n" % e)
        break
    # create a list with all current stations name
    current_stations_name_list = []
    for station in devices_list:
        current_stations_name_list.append(station.name)

    return current_stations_name_list


def create_station(station_name, type='automatic-station'):
    device = swagger_client.Device(name=station_name, type=type)
    created_device_id = ''
    while True:
        try:
            api_response = device_controller_api_inst.save_device_using_post(device)
            created_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print('station already exists!')
                print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        break
    return created_device_id


def get_station_access_token(device_id):
    device_access_token= ''
    # get device credentials
    while True:
        try:
            api_response = device_controller_api_inst.get_device_credentials_by_device_id_using_get(device_id)
            device_access_token = api_response.credentials_id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
        break
    return device_access_token


def set_station_attributes(access_token, attributes):
    # post station attributes
    while True:
        try:
            api_response = device_api_controller_api_inst.post_device_attributes_using_post(access_token, attributes)
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceApiControllerApi->post_device_attributes_using_post: %s\n" % e)
        break


def create_asset_old(asset_name, type='STATE'):
    asset = swagger_client.Asset()
    asset.name = asset_name
    asset.type = type
    try:
        api_response = asset_controller_api_inst.save_asset_using_post(asset)
    except ApiException as e:
        print("Exception when calling AssetControllerApi->save_asset_using_post: %s\n" % e)

    return api_response.id.id

def get_asset_id(asset_name):
    # get state entity id
    asset_name = asset_name
    try:
        # getTenantAssets
        api_response = asset_controller_api_inst.get_tenant_assets_using_get('1', text_search=asset_name)
    except ApiException as e:
        print("Exception when calling AssetControllerApi->get_tenant_assets_using_get: %s\n" % e)
    # if not state does not exist, create it and start a relation with region 'Especiais'
    if not api_response.data:
        state_asset_id = create_asset(asset_name)
        entityId = swagger_client.EntityId('ASSET', state_asset_id)
        set_relation(get_asset_id('Especiais'), entityId)
    else:
        state_asset_id = api_response.data[0].id.id
        entityId = swagger_client.EntityId('ASSET', state_asset_id)

    return entityId


def set_relation(from_id, to_id, relation_type='Contains'):
    relation = swagger_client.EntityRelation()
    relation.type = relation_type
    relation._from = from_id
    relation.to = to_id
    try:
        entity_relation_controller_api_inst.save_relation_using_post(relation)
    except ApiException as e:
        print("Exception when calling EntityRelationControllerApi->save_relation_using_post: %s\n" % e)


def main():
    # get INMET html stations metadata
    stations_metadata = get_inmet_stations_metadata(cfg_params)
    # get INMET root asset
    get_inmet_root_asset_id()
    # get current inmet stations names from TB
    # current_stations_in_tb = get_tb_inmet_current_stations(cfg_params)
    current_stations_in_tb = []
    # verify whether a new station exists
    new_stations = []
    for station in stations_metadata:
        # if there is a new station loads its metadata in TB
        if station['stationCode'] not in current_stations_in_tb:
            new_stations.append(station)
    # create new stations at TB
    for station in new_stations:
        attributes = ast.literal_eval(json.dumps(station, ensure_ascii=False))
        device_id = create_station(station['stationCode'])
        access_token = get_station_access_token(device_id)
        set_station_attributes(access_token, attributes)
        set_relation(get_asset_id(station['stationState']), swagger_client.EntityId('DEVICE', id=device_id))


if __name__ == '__main__':
    main()

