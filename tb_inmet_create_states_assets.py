#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import swagger_client
from swagger_client.rest import ApiException
from tb_inmet_utils import get_api_tokens_from_password
import yaml

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
states_on_regions = {'Norte':['AC','AP','AM','PA','RO','RR','TO'],
                     'Nordeste':['AL','BA','CE','MA','PB','PE','PI','RN','SE'],
                     'Sul':['PR','RS','SC'],
                     'Sudeste':['ES','MG','RJ','SP'],
                     'Centro-Oeste':['DF','GO','MT','MS']}

# create an instance of the API class
asset_controller_api_inst = swagger_client.AssetControllerApi(swagger_client.ApiClient(configuration))

asset = swagger_client.Asset() # Asset | asset

# iterates over all regions and states for creating assets
for k, v in states_on_regions.iteritems():
    for state in v:
        asset.name = state
        asset.type = 'STATE'
        try:
            # saveAsset
            api_response = asset_controller_api_inst.save_asset_using_post(asset)
            print('created asset %s' % state)
        except ApiException as e:
            print("Exception when calling AssetControllerApi->save_asset_using_post: %s\n" % e)