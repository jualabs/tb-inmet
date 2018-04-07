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
import sys
from tb_inmet_utils import get_api_configuration
from tb_inmet_utils import renew_token

# data files root folder
root_path = '/Users/victormedeiros/Downloads/inmet/inmet/data/'
# get API configuration object
configuration = get_api_configuration(hostname='192.168.25.105:8080')

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
        while True:
            try:
                # get device id
                api_response = device_controller_api_inst.get_tenant_device_using_get(station_code)
                #pprint(api_response)
                current_device_id = api_response.id.id
            except ApiException as e:
                if(json.loads(e.body)['message'] == 'Token has expired'):
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
                #pprint(api_response)
                current_device_token = api_response.credentials_id
            except ApiException as e:
                if(json.loads(e.body)['message'] == 'Token has expired'):
                    renew_token(configuration)
                    continue
                else:
                    print("Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
            break
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
            a = sys.getsizeof(json_str)
            json_data = ast.literal_eval(json_str)
            # 2 - write data
            while True:
                try:
                    # post telemetry data
                    api_response = device_api_controller_api_inst.post_telemetry_using_post(current_device_token, json_data)
                    #pprint(api_response)
                except ApiException as e:
                    if (json.loads(e.body)['message'] == 'Token has expired'):
                        renew_token(configuration)
                        continue
                    else:
                        print("Exception when calling DeviceApiControllerApi->post_telemetry_using_post: %s\n" % e)
                break