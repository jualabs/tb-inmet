#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import swagger_client
from swagger_client.rest import ApiException
from tb_inmet_utils import get_api_tokens_from_password
from tb_inmet_utils import renew_token
import ast
import csv
import json
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

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))

reader = csv.reader(csv_file, delimiter=',')
# iterate over all csv data
for row_of_values in reader:
    # 1 - get device id from station code
    if(row_of_values[0][0] != 'A'):
        continue
    current_device_id = ""
    print('start processing station: %s\n' % row_of_values[0])
    while True:
        try:
            # get device id
            api_response = device_controller_api_inst.get_tenant_device_using_get(row_of_values[0])
            current_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                # TODO: create device when it is not found? ask Professor Dr. Goncalves
                print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        break
    # 2 - get device token from device id
    current_device_token = ""
    while True:
        try:
            # getDeviceCredentialsByDeviceId
            api_response = device_controller_api_inst.get_device_credentials_by_device_id_using_get(current_device_id)
            current_device_token = api_response.credentials_id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print(
                    "Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
        break

    # format json with device attributes
    current_data = {}
    current_data['stationName'] = row_of_values[2]
    json_data = ast.literal_eval(json.dumps(current_data, ensure_ascii=False))
    # post station attributes
    while True:
        try:
            # postDeviceAttributes
            api_response = device_api_controller_api_inst.post_device_attributes_using_post(current_device_token,
                                                                                            json_data)
            print('station created!')
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceApiControllerApi->post_device_attributes_using_post: %s\n" % e)
        break
csv_file.close()