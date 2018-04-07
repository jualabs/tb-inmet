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
data = load_csv("stations.csv", header_row=0)
#print("The keys are: %s" % data.keys())
#print(data)
# get API configuration object
configuration = get_api_configuration(hostname='192.168.25.105:8080')

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))

# device_name = 'CruzeirodoSul-A108'
# try: 
#     # saveDevice
#     api_response = device_controller_api_inst.get_tenant_device_using_get(device_name)
#     pprint(api_response)
#     current_device_id = api_response.id.id
# except ApiException as e:
#     print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
         
# loop through all station in metadata file
for i in range(0, len(data['stationName'])):
    # print(data['stationName'][i]+'-'+data['stationCode'][i])
    # create a device for the current station
    current_device_id = ""
    device_name = data['stationCode'][i]

    while True:
        try:
            # saveDevice
            api_response = device_controller_api_inst.get_tenant_device_using_get(device_name)
            pprint(api_response)
            current_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        break
    # delete the current device credentials
    while True:
        try:
            # deleteDevice
            device_controller_api_inst.delete_device_using_delete(current_device_id)
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceControllerApi->delete_device_using_delete: %s\n" % e)
        break