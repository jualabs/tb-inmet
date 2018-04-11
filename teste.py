#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import calendar
import swagger_client
from swagger_client.rest import ApiException
import ast
import os
import glob
import csv
import json
import sys
from tb_inmet_utils import get_api_configuration
from tb_inmet_utils import renew_token
from tqdm import tqdm
import collections

# get API configuration object
configuration = get_api_configuration(hostname='192.168.25.105:8080', username='victorwcm@gmail.com', password='')

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))

# 1 - get device id from station code
station_code = "teste"
current_device_id = ""
while True:
    try:
        # get device id
        api_response = device_controller_api_inst.get_tenant_device_using_get(station_code)
        # pprint(api_response)
        current_device_id = api_response.id.id
    except ApiException as e:
        if (json.loads(e.body)['message'] == 'Token has expired'):
            renew_token(configuration)
            continue
        else:
            print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
    break
# 2 - get device token from device id
current_device_token = ""
while True:
    try:
        # getDeviceCredentialsByDeviceId
        api_response = device_controller_api_inst.get_device_credentials_by_device_id_using_get(current_device_id)
        # pprint(api_response)
        current_device_token = api_response.credentials_id
    except ApiException as e:
        if (json.loads(e.body)['message'] == 'Token has expired'):
            renew_token(configuration)
            continue
        else:
            print(
                "Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
    break
# write data to thingsboard
# 1 - format json
json_data = {'float':1.5, 'ínt':1, 'str':'str'}
# 2 - write data
while True:
    try:
        # post telemetry data
        api_response = device_api_controller_api_inst.post_telemetry_using_post(current_device_token, json_data)
        # pprint(api_response)
        print('wrote data for station %s')
    except ApiException as e:
        if (json.loads(e.body)['message'] == 'Token has expired'):
            renew_token(configuration)
            continue
        else:
            print("Exception when calling DeviceApiControllerApi->post_telemetry_using_post: %s\n" % e)
    break