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
configuration.api_key['X-Authorization'] = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ2aWN0b3J3Y21AZ21haWwuY29tIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJ1c2VySWQiOiI2MmJkMGFmMC0xMjc1LTExZTgtYmI4NS03NWQ4MTIxM2VjMjUiLCJmaXJzdE5hbWUiOiJWaWN0b3IiLCJsYXN0TmFtZSI6Ik1lZGVpcm9zIiwiZW5hYmxlZCI6dHJ1ZSwiaXNQdWJsaWMiOmZhbHNlLCJ0ZW5hbnRJZCI6ImZhYWYwMzAwLTEyNzQtMTFlOC1iYjg1LTc1ZDgxMjEzZWMyNSIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAiLCJpc3MiOiJ0aGluZ3Nib2FyZC5pbyIsImlhdCI6MTUyMjEwNjU5NywiZXhwIjoxNTMxMTA2NTk3fQ.NgHYcsINK5RB2vhlbb4oJUI60SKH3WRHEEWjLeWjUngh-se4c0T0gZmN00Be5m2LUBKyzFibkNBsD01XmThUPg'
configuration.api_key_prefix['X-Authorization'] = 'Bearer'
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
    device_name = data['stationName'][i] + '-' + data['stationCode'][i]
    try: 
        # saveDevice
        api_response = device_controller_api_inst.get_tenant_device_using_get(device_name)
        pprint(api_response)
        current_device_id = api_response.id.id
    except ApiException as e:
        print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
    # delete the current device credentials
    try: 
        # deleteDevice
        device_controller_api_inst.delete_device_using_delete(current_device_id)
    except ApiException as e:
        print("Exception when calling DeviceControllerApi->delete_device_using_delete: %s\n" % e)