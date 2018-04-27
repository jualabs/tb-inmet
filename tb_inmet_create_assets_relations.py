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
entity_relation_controller_api_inst = swagger_client.EntityRelationControllerApi(swagger_client.ApiClient(configuration))

asset = swagger_client.Asset() # Asset | asset
relation = swagger_client.EntityRelation() # EntityRelation | relation
relation.type = 'Contains'

# iterates over all regions and states for creating assets
for k, v in states_on_regions.iteritems():
    # get region entity id
    asset_name = k
    try:
        # getTenantAssets
        api_response = asset_controller_api_inst.get_tenant_assets_using_get('1', text_search=asset_name)
        print('founded asset %s' % asset_name)
    except ApiException as e:
        print("Exception when calling AssetControllerApi->get_tenant_assets_using_get: %s\n" % e)
    entityId = swagger_client.EntityId('ASSET', id=api_response.data[0].id.id)
    relation._from = entityId
    for state in v:
        # get state entity id
        asset_name = state
        try:
            # getTenantAssets
            api_response = asset_controller_api_inst.get_tenant_assets_using_get('1', text_search=asset_name)
            print('founded asset %s' % asset_name)
        except ApiException as e:
            print("Exception when calling AssetControllerApi->get_tenant_assets_using_get: %s\n" % e)
        entityId = swagger_client.EntityId('ASSET', id=api_response.data[0].id.id)
        relation.to = entityId
        try:
            # saveAsset
            entity_relation_controller_api_inst.save_relation_using_post(relation)
            print('created relation %s' % (k + '->' + state))
        except ApiException as e:
            print("Exception when calling EntityRelationControllerApi->save_relation_using_post: %s\n" % e)