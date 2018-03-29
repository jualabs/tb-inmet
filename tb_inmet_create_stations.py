#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
from tb_inmet_utils import load_csv
import ast

# read data related to stations metadata
data = load_csv("stations.csv", header_row=0)
#print("The keys are: %s" % data.keys())
#print(data)

# Configure API key authorization: X-Authorization
configuration = swagger_client.Configuration()
configuration.api_key['X-Authorization'] = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ2aWN0b3J3Y21AZ21haWwuY29tIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJ1c2VySWQiOiIxNDZmMTBmMC0zMjkxLTExZTgtYjFiNy0wNTdkMWEyZGY0MzAiLCJmaXJzdE5hbWUiOiJWaWN0b3IiLCJsYXN0TmFtZSI6Ik1lZGVpcm9zIiwiZW5hYmxlZCI6dHJ1ZSwiaXNQdWJsaWMiOmZhbHNlLCJ0ZW5hbnRJZCI6IjlkMWE1YzMwLTMyOTAtMTFlOC1iMWI3LTA1N2QxYTJkZjQzMCIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAiLCJpc3MiOiJ0aGluZ3Nib2FyZC5pbyIsImlhdCI6MTUyMjI2MDQ2MCwiZXhwIjoxNTIyMjYxMzYwfQ.RU6KXwCUFzUwa4HBljFtV_uo3SB1p42CGidmMKKXXe4uU7BgfcceplLTOeWf6kvMAxA9Wff-cC0naeeR5LHZRA'
configuration.api_key_prefix['X-Authorization'] = 'Bearer'
configuration.host = 'http://f6439f36.ngrok.io'
# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))
 
# loop through all station in metadata file
for i in range(0, len(data['stationName'])):
    # print(data['stationName'][i]+'-'+data['stationCode'][i])
    # create a device for the current station
    device_name = data['stationCode'][i]
    device = swagger_client.Device(name=device_name, type='automatic-station')
    try: 
        # saveDevice
        print('creating station ' + data['stationName'][i] + ' - ' + data['stationCode'][i] + '...')
        api_response = device_controller_api_inst.save_device_using_post(device)
        current_device_id = api_response.id.id
    except ApiException as e:
        print('station already exists!')
        print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        continue
    # get the current device credentials
    try: 
      
    # getDeviceCredentialsByDeviceId
        api_response = device_controller_api_inst.get_device_credentials_by_device_id_using_get(current_device_id)
        current_device_token = api_response.credentials_id
    except ApiException as e:
        print("Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
     
    #format json with device attributes
    json_str = '{'
    for k, v in data.items():
        json_str += '\'' + k + '\'' + ':' + '\'' + str(data[k][i]) +'\'' + ','
    json_str = json_str[:-1] + '}'
    json_data = ast.literal_eval(json_str)
     
    # post station attributes
    try: 
        # postDeviceAttributes
        api_response = device_api_controller_api_inst.post_device_attributes_using_post(current_device_token, json_data)
        print('station created!')
    except ApiException as e:
        print("Exception when calling DeviceApiControllerApi->post_device_attributes_using_post: %s\n" % e)