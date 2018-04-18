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
#root_path = '/home/tb-inmet/inmet/inmet/inmet/data/'
# get API configuration object
#configuration = get_api_configuration(hostname='192.168.25.105:8080', username='victorwcm@gmail.com', password='')
configuration = get_api_configuration(hostname='127.0.0.1:8080', username='victorwcm@gmail.com', password='')

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))

def send_data_from_file(file_path):
    file = open(file_path, 'r')
    single_str = ''
    for line in file:
        single_str += line
    single_str = single_str.replace('\r\n', '')
    single_str = single_str.replace(' ', '')
    single_str = single_str.replace('\t', '')
    data = single_str.split('<br>')
    data = data[:-1]
    # get station code
    station_code = file_path.split('.')[0].split('-')[-1]
    # init DEBUG
    if (station_code != 'A239'):
        return
    # end DEBUG
    # 1 - get device id from station code
    current_device_id = ""
    tqdm.write('start processing file: %s\n' % file_path.split('/')[-1])
    while True:
        try:
            # get device id
            api_response = device_controller_api_inst.get_tenant_device_using_get(station_code)
            current_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                tqdm.write("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
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
                tqdm.write(
                    "Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
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
        ts_utc = int(calendar.timegm(time_tuple_utc)) * 1000
        json_temp = {'invalid_sensors':''}
        # adjust data types
        for key, value in current_data.iteritems():
            if (key == 'hora' or key == 'vento_vel' or key == 'umid_max' or key == 'umid_min' or key == 'umid_inst'):
                try:
                    json_temp[key] = int(current_data[key])
                except ValueError:
                    json_temp['invalid_sensors'] = (key + ',');
                    current_data[key] = '-';
                    tqdm.write('value not provided in file: %s at hour %s' % (file_path, current_data['hora']))
                    continue
            elif (key == 'radiacao' or key == 'precipitacao' or key == 'vento_direcao' or key == 'vento_rajada' or
                  key == 'temp_max' or key == 'temp_min' or key == 'temp_inst' or
                  key == 'pressao_max' or key == 'pressao_min' or key == 'pressao' or
                  key == 'pto_orvalho_max' or key == 'pto_orvalho_min' or key == 'pto_orvalho_inst'):
                try:
                    json_temp[key] = float(current_data[key])
                except ValueError:
                    json_temp['invalid_sensors'] = (key + ',');
                    current_data[key] = '-';
                    tqdm.write('value not provided in file: %s at hour %s' % (file_path, current_data['hora']))
                    continue
        # clean last caracter from json invalid sensors key
        if json_temp['invalid_sensors'] != '':
            json_temp['invalid_sensors'] = json_temp['invalid_sensors'][-1]
        # write data to thingsboard
        # 1 - format json
        json_data = {}
        json_data['values'] = json_temp
        json_data['ts'] = ts_utc
        # 2 - write data
        while True:
            try:
                # post telemetry data
                api_response = device_api_controller_api_inst.post_telemetry_using_post(current_device_token, json_data)
                tqdm.write('wrote data for station %s' % current_data['codigo_estacao'])
            except ApiException as e:
                if (json.loads(e.body)['message'] == 'Token has expired'):
                    renew_token(configuration)
                    continue
                else:
                    tqdm.write("Exception when calling DeviceApiControllerApi->post_telemetry_using_post: %s\n" % e)
            break
    file.close()

def walkdir(folder):
    # walk through each files in a directory
    for dirpath, dirs, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".html"):
                yield os.path.abspath(os.path.join(dirpath, filename))

# function that iterates over all folders
def iterate_over_all_files(root_path):
    # compute the total number of files
    file_counter = 0
    for file_path in walkdir(root_path):
        file_counter += 1
    # iterates over all files
    with tqdm(total=file_counter, unit='files') as pbar:
        for file_path in walkdir(root_path):
            send_data_from_file(file_path)
            pbar.set_postfix(file=file_path, refresh=False)
            pbar.update()

iterate_over_all_files(root_path)