#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
from tb_inmet_utils import load_csv
from tb_inmet_utils import get_api_configuration
from tb_inmet_utils import renew_token

import ast

# read data related to stations metadata
data = load_csv("stations.csv", header_row=0, delimiter=';')
# get API configuration object
configuration = get_api_configuration(hostname='192.168.25.105:8080')

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))
 
# loop through all station in metadata file
for i in range(0, len(data['stationName'])):
    # print(data['stationName'][i]+'-'+data['stationCode'][i])
    # create a device for the current station
    device_name = data['stationCode'][i]
    device = swagger_client.Device(name=device_name, type='automatic-station')
    while True:
        try:
            # saveDevice
            print('creating station ' + data['stationName'][i] + ' - ' + data['stationCode'][i] + '...')
            api_response = device_controller_api_inst.save_device_using_post(device)
            current_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print('station already exists!')
                print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        break
    # get the current device credentials
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
                print("Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
        break
    #format json with device attributes
    json_str = '{'
    for k, v in data.items():
        json_str += '\'' + k + '\'' + ':' + '\'' + str(data[k][i]) +'\'' + ','
    json_str = json_str[:-1] + '}'
    json_data = ast.literal_eval(json_str)
     
    # post station attributes
    while True:
        try:
            # postDeviceAttributes
            api_response = device_api_controller_api_inst.post_device_attributes_using_post(current_device_token, json_data)
            print('station created!')
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceApiControllerApi->post_device_attributes_using_post: %s\n" % e)
        break
