#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from datetime import datetime
import time
import calendar
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
import ast
import os
import glob
import csv
import json

# data files root folder
root_path = '/Users/victormedeiros/Downloads/inmet/inmet/data/'
# configure API key authorization: X-Authorization
configuration = swagger_client.Configuration()
configuration.api_key['X-Authorization'] = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ2aWN0b3J3Y21AZ21haWwuY29tIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJ1c2VySWQiOiIxNDZmMTBmMC0zMjkxLTExZTgtYjFiNy0wNTdkMWEyZGY0MzAiLCJmaXJzdE5hbWUiOiJWaWN0b3IiLCJsYXN0TmFtZSI6Ik1lZGVpcm9zIiwiZW5hYmxlZCI6dHJ1ZSwiaXNQdWJsaWMiOmZhbHNlLCJ0ZW5hbnRJZCI6IjlkMWE1YzMwLTMyOTAtMTFlOC1iMWI3LTA1N2QxYTJkZjQzMCIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAiLCJpc3MiOiJ0aGluZ3Nib2FyZC5pbyIsImlhdCI6MTUyMjg2NzIzNywiZXhwIjoxNTIyODY4MTM3fQ.t2YLJFJZwsOREf1oXoM19y1HlhWn_4sSd7rCbE_kkf1c59jbVDSt7ox3Fn6TmCSvNsunhcZcVyDp5YGr1iwwmA'
configuration.api_key_prefix['X-Authorization'] = 'Bearer'
configuration.host = 'http://79005d63.ngrok.io'
# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))

# iterates over all folders
for folder in os.listdir(root_path):
    current_folder_path = root_path + folder
    # iterates over all '.html' files in one folder
    for filename in glob.glob(os.path.join(current_folder_path, '*.html')):
        file = open(filename, 'r')
        single_str = ''
        for line in file:
            single_str += line
        single_str = single_str.replace('\r\n','')
        single_str = single_str.replace(' ', '')
        single_str = single_str.replace('\t', '')
        data = single_str.split('<br>')
        data = data[:-1]
        # first iterates just to discover station code
        reader = csv.reader(data)
        keys = reader.next()
        values = reader.next()
        current_data = dict(zip(keys, values))
        station_code = current_data['codigo_estacao']
        # 1 - get device id from station code
        current_device_id = ""
        try:
            # get device id
            api_response = device_controller_api_inst.get_tenant_device_using_get(station_code)
            #pprint(api_response)
            current_device_id = api_response.id.id
        except ApiException as e:
            print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        # 2 - get device token from device id
        current_device_token = ""
        try:
            # getDeviceCredentialsByDeviceId
            api_response = device_controller_api_inst.get_device_credentials_by_device_id_using_get(current_device_id)
            #pprint(api_response)
            current_device_token = api_response.credentials_id
        except ApiException as e:
            print(
                "Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
        # with tb credentials collected, send all data
        reader = csv.reader(data)
        keys = reader.next()
        # iterate over data collects, -1 to exclude first row of keys
        for i in range(len(data)-1):
            values = reader.next()
            current_data = dict(zip(keys, values))
            # convert current datetime to timestamp
            date = current_data['data'].split('/')
            time_tuple_utc = (int(date[2]), int(date[1]), int(date[0]), int(current_data['hora']), 0, 0)
            ts_utc  = calendar.timegm(time_tuple_utc)
            # write data to thingsboard
            # 1 - format json
            json_data = {}
            json_data['ts'] = ts_utc
            json_data['values'] = current_data
            json_str = json.dumps(json_data, ensure_ascii=False)
            json_data = ast.literal_eval(json_str)
            # 2 - write data
            try:
                # post telemetry data
                api_response = device_api_controller_api_inst.post_telemetry_using_post(current_device_token, json_data)
                #pprint(api_response)
            except ApiException as e:
                print("Exception when calling DeviceApiControllerApi->post_telemetry_using_post: %s\n" % e)
        break
    break