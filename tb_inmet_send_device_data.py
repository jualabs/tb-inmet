#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import calendar
import swagger_client
from swagger_client.rest import ApiException
import os
import csv
import json
from tb_inmet_utils import get_api_tokens_from_password
from tb_inmet_utils import renew_token
from tqdm import tqdm
import yaml

# get configurations from YAML config file
with open("config.yaml", 'r') as yamlfile:
    cfg = yaml.load(yamlfile)

# set configurations values
# set hostname, username and password from user
configuration = swagger_client.Configuration()
configuration.host = cfg['tb_api_access']['host']
configuration.username = cfg['tb_api_access']['user']
configuration.password = cfg['tb_api_access']['passwd']
# set root path for input data files
root_path = cfg['tb_input_data']['root_folder']
if root_path[-1] != '/':
    root_path = root_path + '/'
# get tokens
tokens = get_api_tokens_from_password(configuration.host, configuration.username, configuration.password)
# configure API key authorization: X-Authorization
configuration.api_key['X-Authorization'] = tokens['token']
configuration.api_key_prefix['X-Authorization'] = 'Bearer'

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
                # TODO: create device when it is not found? ask Professor Dr. Goncalves
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
            if key in ['hora','vento_vel','umid_max','umid_min','umid_inst']:
                try:
                    json_temp[key] = int(current_data[key])
                except ValueError:
                    json_temp['invalid_sensors'] = json_temp['invalid_sensors'] + (key + ',')
                    current_data[key] = '-'
                    tqdm.write('value not provided in file: %s at hour %s' % (file_path, current_data['hora']))
                    continue
            elif key in ['radiacao','precipitacao','vento_direcao','vento_rajada','temp_max','temp_min','temp_inst',
                          'pressao_max','pressao_min','pressao','pto_orvalho_max','pto_orvalho_min','pto_orvalho_inst']:
                try:
                    json_temp[key] = float(current_data[key])
                except ValueError:
                    json_temp['invalid_sensors'] = json_temp['invalid_sensors'] + (key + ',')
                    current_data[key] = '-'
                    tqdm.write('value not provided in file: %s at hour %s' % (file_path, current_data['hora']))
                    continue
        # clean last caracter from json invalid sensors key
        if json_temp['invalid_sensors'] != '':
            json_temp['invalid_sensors'] = json_temp['invalid_sensors'][0:-1]
        # swap wind information due to problem on inmet crawled data vento_direcao <-> vento_vel
        temp_value = json_temp['vento_vel']
        json_temp['vento_vel'] = json_temp['vento_direcao']
        json_temp['vento_direcao'] = temp_value
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