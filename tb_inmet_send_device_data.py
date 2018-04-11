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

# data files root folder
root_path = '/Users/victormedeiros/Downloads/inmet/inmet/data/'
# get API configuration object
configuration = get_api_configuration(hostname='', username='', password='')

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))


# iterates over all folders
for folder in os.listdir(root_path):
    current_folder_path = root_path + folder
    # iterates over all '.html' files in one folder
    for filename in glob.glob(os.path.join(current_folder_path, '*.html')):
        print('processing file: %s\n' % filename.split('/')[-1])
        file = open(filename, 'r')
        single_str = ''
        for line in file:
            single_str += line
        single_str = single_str.replace('\r\n','')
        single_str = single_str.replace(' ', '')
        single_str = single_str.replace('\t', '')
        data = single_str.split('<br>')
        data = data[:-1]
        # get station code
        station_code = filename.split('.')[0].split('-')[-1]
        if (station_code != 'A239'):
            continue
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
        for row_of_values in reader:
            current_data = dict(zip(keys, row_of_values))
            # convert current datetime to timestamp
            date = current_data['data'].split('/')
            time_tuple_utc = (int(date[2]), int(date[1]), int(date[0]), int(current_data['hora']), 0, 0)
            ts_utc  = int(calendar.timegm(time_tuple_utc)) * 1000
            # adjust data types
            if(current_data['hora'] != '////'):
                current_data['hora'] = int(current_data['hora'])
            if (current_data['radiacao'] != '////'):
                current_data['radiacao'] = float(current_data['radiacao'])
            if (current_data['precipitacao'] != '////'):
                current_data['precipitacao'] = float(current_data['precipitacao'])
            if (current_data['vento_direcao'] != '////'):
                current_data['vento_direcao'] = float(current_data['vento_direcao'])
            if (current_data['vento_rajada'] != '////'):
                current_data['vento_rajada'] = float(current_data['vento_rajada'])
            if (current_data['vento_vel'] != '////'):
                current_data['vento_vel'] = int(current_data['vento_vel'])
            if (current_data['temp_max'] != '////'):
                current_data['temp_max'] = float(current_data['temp_max'])
            if (current_data['temp_min'] != '////'):
                current_data['temp_min'] = float(current_data['temp_min'])
            if (current_data['temp_inst'] != '////'):
                current_data['temp_inst'] = float(current_data['temp_inst'])
            if (current_data['umid_max'] != '////'):
                current_data['umid_max'] = int(current_data['umid_max'])
            if (current_data['umid_min'] != '////'):
                current_data['umid_min'] = int(current_data['umid_min'])
            if (current_data['umid_inst'] != '////'):
                current_data['umid_inst'] = int(current_data['umid_inst'])
            if (current_data['pressao_max'] != '////'):
                current_data['pressao_max'] = float(current_data['pressao_max'])
            if (current_data['pressao_min'] != '////'):
                current_data['pressao_min'] = float(current_data['pressao_min'])
            if (current_data['pressao'] != '////'):
                current_data['pressao'] = float(current_data['pressao'])
            if (current_data['pto_orvalho_max'] != '////'):
                current_data['pto_orvalho_max'] = float(current_data['pto_orvalho_max'])
            if (current_data['pto_orvalho_min'] != '////'):
                current_data['pto_orvalho_min'] = float(current_data['pto_orvalho_min'])
            if (current_data['pto_orvalho_inst'] != '////'):
                current_data['pto_orvalho_inst'] = float(current_data['pto_orvalho_inst'])
            # write data to thingsboard
            # 1 - format json
            json_data = {}
            json_data['values'] = current_data
            json_data['ts'] = ts_utc
            # 2 - write data
            while True:
                try:
                    # post telemetry data
                    api_response = device_api_controller_api_inst.post_telemetry_using_post(current_device_token, json_data)
                    #pprint(api_response)
                    print('wrote data for station %s' % current_data['codigo_estacao'])
                except ApiException as e:
                    if (json.loads(e.body)['message'] == 'Token has expired'):
                        renew_token(configuration)
                        continue
                    else:
                        print("Exception when calling DeviceApiControllerApi->post_telemetry_using_post: %s\n" % e)
                break
file.close()