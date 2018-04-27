#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import swagger_client
from swagger_client.rest import ApiException
from tb_inmet_utils import get_api_tokens_from_password
import csv
import yaml

# read data related to stations metadata
csv_file = open("station-state.csv", 'r')

# get configurations from YAML config file
with open("config.yaml", 'r') as yamlfile:
    cfg = yaml.load(yamlfile)

# set configurations values
# set hostname, username and password from user
configuration = swagger_client.Configuration()
configuration.host = cfg['tb_api_access']['host']
configuration.username = cfg['tb_api_access']['user']
configuration.password = cfg['tb_api_access']['passwd']

# get tokens
tokens = get_api_tokens_from_password(configuration.host, configuration.username, configuration.password)
# configure API key authorization: X-Authorization
configuration.api_key['X-Authorization'] = tokens['token']
configuration.api_key_prefix['X-Authorization'] = 'Bearer'

# define regions and states
states_on_regions = {'AC':0,'AP':0,'AM':0,'PA':0,'RO':0,'RR':0,'TO':0,
                     'AL':0,'BA':0,'CE':0,'MA':0,'PB':0,'PE':0,'PI':0,'RN':0,'SE':0,
                     'PR':0,'RS':0,'SC':0,
                     'ES':0,'MG':0,'RJ':0,'SP':0,
                     'DF':0,'GO':0,'MT':0,'MS':0}


# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))
asset_controller_api_inst = swagger_client.AssetControllerApi(swagger_client.ApiClient(configuration))
entity_relation_controller_api_inst = swagger_client.EntityRelationControllerApi(swagger_client.ApiClient(configuration))

asset = swagger_client.Asset() # Asset | asset
relation = swagger_client.EntityRelation() # EntityRelation | relation
relation.type = 'Contains'

# iterates over all regions and states gathering EntityIDs for all states
for state, v in states_on_regions.iteritems():
    # get state entity id
    asset_name = state
    try:
        # getTenantAssets
        api_response = asset_controller_api_inst.get_tenant_assets_using_get('1', text_search=asset_name)
        print('founded asset %s' % asset_name)
    except ApiException as e:
        print("Exception when calling AssetControllerApi->get_tenant_assets_using_get: %s\n" % e)
    entityId = swagger_client.EntityId('ASSET', id=api_response.data[0].id.id)
    states_on_regions[state] = entityId

# iterates over all stations gathering EntityIDs and creating relations with states
reader = csv.reader(csv_file, delimiter=',')
missing_stations = 0
# iterate over all csv data
for row_of_values in reader:
    if(row_of_values[0][0] != 'A'):
        continue
    device_name = row_of_values[0]
    device_state = row_of_values[1]
    # get device id
    try:
        api_response = device_controller_api_inst.get_tenant_device_using_get(device_name)
        print('founded device %s' % device_name)
    except ApiException as e:
        print('not found %s' % device_name)
        print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        missing_stations = missing_stations + 1

    entityId = swagger_client.EntityId('DEVICE', id=api_response.id.id)
    relation._from = states_on_regions[device_state]
    relation.to = entityId

    try:
        entity_relation_controller_api_inst.save_relation_using_post(relation)
        print('created relation %s' % (device_state + '->' + device_name))
    except ApiException as e:
        print("Exception when calling EntityRelationControllerApi->save_relation_using_post: %s\n" % e)

print (missing_stations)
csv_file.close()