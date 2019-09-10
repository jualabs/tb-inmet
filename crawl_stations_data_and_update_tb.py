#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import swagger_client
from swagger_client.rest import ApiException
from tb_inmet_utils import renew_token
from tb_inmet_utils import get_tb_api_configuration
import json
import requests
import urllib
import yaml
import ast
import sys
import argparse
import os.path
from datetime import datetime, timedelta
import csv
import calendar
import tqdm
from lxml import html
import base64
import time

# load configurations from YAML config file
with open("config.yaml", 'r') as yamlfile:
    cfg_params = yaml.load(yamlfile)

# get API access configuration object
configuration = get_tb_api_configuration(cfg_params)

# create instances of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device_api_controller_api_inst = swagger_client.DeviceApiControllerApi(swagger_client.ApiClient(configuration))
asset_controller_api_inst = swagger_client.AssetControllerApi(swagger_client.ApiClient(configuration))
entity_relation_controller_api_inst = swagger_client.EntityRelationControllerApi(swagger_client.ApiClient(configuration))


def is_valid_file(arg_file_str):
    if not os.path.exists(arg_file_str):
        msg = "The file %s does not exist!" % arg_file_str
        raise argparse.ArgumentTypeError(msg)
    else:
        # return an open file handle
        return open(arg_file_str, 'r')


def is_valid_date(arg_date_str):
    try:
        return datetime.strptime(arg_date_str, "%d-%m-%Y")
    except ValueError:
        msg = "Given date ({0}) not valid! Expected format, DD-MM-YYYY!".format(arg_date_str)
        raise argparse.ArgumentTypeError(msg)


def create_parser():
    parser = argparse.ArgumentParser(
        description='Starts a crawler on INMET and transfers data to ThingsBoard'
    )

    parser.add_argument(
        '-d', '--input-data-path', dest='input_data_path', type=is_valid_file, required=False, default=None,
        help='Path to folder containing \'.html\' files with INMET stations data. If this argument is set no other '
             'argument is considered.'
    )

    parser.add_argument(
        '-i', '--input-stations-file', dest='input_stations_file', type=is_valid_file, required=False, default=None,
        help='File with a list of desired INMET stations (one name per row). Fetch all available stations data ' +
             'if no file provided'
    )

    parser.add_argument(
        '-s', '--start-date', dest='start_date', type=is_valid_date, required=False, default=None,
        help='Date in which data fetch will start on DD-MM-YYYY format. If no date provided, mostRecentUpdate ' +
             'attribute on ThingsBoard will be considered for each station.'
    )

    parser.add_argument(
        '-e', '--end-date', dest='end_date', type=is_valid_date, required=False, default=None,
        help='Date in which data fetch will stop on DD-MM-YYYY format. If no date provided, the day of today ' +
             'will be considered for each station.'
    )
    return parser


def get_current_stations(cfg_params):

    relation_search_parameters = swagger_client.RelationsSearchParameters(
        root_id=cfg_params['tb_entities_access']['root_asset_id'], root_type='ASSET', direction='FROM', max_level=0)
    query = swagger_client.DeviceSearchQuery(device_types=['automatic-station'], parameters=relation_search_parameters,
                                             relation_type='Contains')
    query.parameters = relation_search_parameters

    while True:
        try:
            stations_list = device_controller_api_inst.find_by_query_using_post1(query)
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceControllerApi->find_by_query_using_post1: %s\n" % e)
        break

    return stations_list


def get_station(cfg_params, station_name):
    current_device_id = ''
    # first get the device id
    while True:
        try:
            api_response = device_controller_api_inst.get_tenant_device_using_get(station_name)
            current_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                # TODO: create device when it is not found? ask Professor Dr. Goncalves
                print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
        break
    # second get the device from device id
    try:
        devices = device_controller_api_inst.get_devices_by_ids_using_get(current_device_id)
    except ApiException as e:
        print("Exception when calling DeviceControllerApi->get_devices_by_ids_using_get: %s\n" % e)

    return devices[0]


def get_station_token(station_id):
    # get device token
    device_token = ''
    while True:
        try:
            api_response = device_controller_api_inst.get_device_credentials_by_device_id_using_get(station_id)
            device_token = api_response.credentials_id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print(
                    "Exception when calling DeviceControllerApi->get_device_credentials_by_device_id_using_get: %s\n" % e)
        break
    return device_token

# API version
'''
def get_station_attributes(station_token):

    client_keys = 'url,mostRecentData'
    station_attributes = ''
    try:
        api_response = device_api_controller_api_inst.get_device_attributes_using_get(station_token, shared_keys=client_keys)
        print(api_response)
    except ApiException as e:
        print("Exception when calling DeviceApiControllerApi->get_device_attributes_using_get: %s\n" % e)

    return station_attributes
'''

# requests version
def get_station_attributes(station_token):
    client_keys = 'url,mostRecentData'
    url = 'http://'+ cfg_params['tb_api_access']['host'] + '/api/v1/' + station_token + '/attributes?clientKeys=' + client_keys
    r = requests.get(url)
    return ast.literal_eval(r.content)

def set_station_attributes(station_token, attributes):
    # set station attributes
    while True:
        try:
            api_response = device_api_controller_api_inst.post_device_attributes_using_post(station_token, attributes)
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                print("Exception when calling DeviceApiControllerApi->post_device_attributes_using_post: %s\n" % e)
        break


def format_data(rawData):
    single_str = ''
    for line in rawData:
        single_str += line
    single_str = single_str.replace('\r\n', '')
    single_str = single_str.replace(' ', '')
    single_str = single_str.replace('\t', '')
    data = single_str.split('<br>')
    data = data[:-1]

    return data


def run_crawler(start_date, end_date, url):

    # first get base page
    resp = requests.get(url)
    tree = html.fromstring(resp.content)
    aleaValue = tree.xpath('//input[@type="hidden" and @name="aleaValue"]/@value')[0]
    xaleaValue = tree.xpath('//input[@type="hidden" and @name="xaleaValue"]/@value')[0]
    xID = tree.xpath('//input[@type="hidden" and @name="xID"]/@value')[0]
    aleaNum = int(base64.b64decode(aleaValue))
    # define time period and create session
    form = {
        'dtaini': start_date.strftime("%d/%m/%Y"),
        'dtafim': end_date.strftime("%d/%m/%Y"),
        'aleaValue': aleaValue,
        'aleaNum': aleaNum,
        'xaleaValue': xaleaValue,
        'xID': xID
    }
    encondedForm = urllib.urlencode(form)
    head = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post(url, data=encondedForm, headers=head)

    # get session cookie and get data from site
    cookie = r.headers["Set-Cookie"]
    head = {
        'Cookie': cookie
    }
    fixed_url = 'http://www.inmet.gov.br/sonabra/pg_downDadosCodigo_sim.php'
    r = requests.get(fixed_url, headers=head)

    formatted_data = format_data(r)

    return formatted_data


def load_station_data(station_token, station_data):
    # load station data
    reader = csv.reader(station_data)
    keys = reader.next()
    # iterate over data collects
    for i, row_of_values in enumerate(reader, start = 0):
        current_data = dict(zip(keys, row_of_values))
        most_recent_data = ''
        # get date from the most recent data for attribute update
        if i == 0:
            most_recent_data = current_data['data'].replace('/','-')
        # convert current datetime to timestamp
        date = current_data['data'].split('/')
        time_tuple_utc = (int(date[2]), int(date[1]), int(date[0]), int(current_data['hora']), 0, 0)
        ts_utc = int(calendar.timegm(time_tuple_utc)) * 1000
        json_temp = {'unavailable_data': ''}
        # adjust data types
        for key, value in current_data.iteritems():
            if key in ['hora', 'vento_vel', 'umid_max', 'umid_min', 'umid_inst']:
                try:
                    json_temp[key] = int(current_data[key])
                except ValueError:
                    json_temp['unavailable_data'] = json_temp['unavailable_data'] + (key + ',')
                    current_data[key] = '-'
                    continue
            elif key in ['radiacao', 'precipitacao', 'vento_direcao', 'vento_rajada', 'temp_max', 'temp_min',
                         'temp_inst',
                         'pressao_max', 'pressao_min', 'pressao', 'pto_orvalho_max', 'pto_orvalho_min',
                         'pto_orvalho_inst']:
                try:
                    json_temp[key] = float(current_data[key])
                except ValueError:
                    json_temp['unavailable_data'] = json_temp['unavailable_data'] + (key + ',')
                    current_data[key] = '-'
                    continue
        # clean last character from json unavailable_data key
        if json_temp['unavailable_data'] != '':
            json_temp['unavailable_data'] = json_temp['unavailable_data'][0:-1]
        # swap wind information due to problem on inmet crawled data vento_direcao <-> vento_vel
        wind_direction = ''
        wind_speed = ''
        if 'vento_vel' in json_temp:
            wind_direction = json_temp['vento_vel']
            json_temp.pop('vento_vel')
        if 'vento_direcao' in json_temp:
            wind_speed = json_temp['vento_direcao']
            json_temp.pop('vento_direcao')
        if wind_direction != '':
            json_temp['vento_direcao'] = wind_direction
        if wind_speed != '':
            json_temp['vento_vel'] = wind_speed
        # write data to thingsboard
        # 1 - format json
        json_data = {}
        json_data['values'] = json_temp
        json_data['ts'] = ts_utc
        # 2 - write data
        while True:
            try:
                # time.sleep(0.5)
                api_response = device_api_controller_api_inst.post_telemetry_using_post(station_token, json_data)
            except ApiException as e:
                if (json.loads(e.body)['message'] == 'Token has expired'):
                    renew_token(configuration)
                    continue
                else:
                    print("Exception when calling DeviceApiControllerApi->post_telemetry_using_post: %s\n" % e)
            break
    # update mostRecentData attribute
    json_data = {}
    json_data = {'mostRecentData':most_recent_data}
    set_station_attributes(station_token, json_data)
    pass


def walkdir(folder):
    # walk through each files in a directory
    for dirpath, dirs, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".html"):
                yield os.path.abspath(os.path.join(dirpath, filename))

def send_data_from_file(file_path):
    file = open(file_path, 'r')
    formatted_data = format_data(file)
    # get station code
    station_code = file_path.split('.')[0].split('-')[-1]
    # 1 - get device id from station code
    current_device_id = ""
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
    load_station_data(current_device_token, formatted_data)

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

def main():
    '''
    run_crawler(datetime.today(), datetime.today(),
                'http://www.inmet.gov.br/sonabra/pg_dspDadosCodigo_sim.php?QTMwMQ==')
    '''
    parser = create_parser()
    args = parser.parse_args()
    stations = []
    # verify if there is a path with input files
    if args.input_data_path:
        file_counter = 0
        for filename in walkdir(args.input_data_path):
            file_counter += 1
        # iterates over all files
        with tqdm(total=file_counter, unit='files') as pbar:
            for filename in walkdir(args.input_data_path):
                send_data_from_file(filename)
                pbar.set_postfix(file=filename, refresh=False)
                pbar.update()
    else:
        # verify if there is a file with a list of stations
        if args.input_stations_file:
            # if so, read file to a list
            file_content = args.input_stations_file.readlines()
            file_content = [x.strip() for x in file_content]
            # query defined stations
            for station_name in file_content:
                stations.append(get_station(cfg_params, station_name))
        else:
            # query all stations
            stations = get_current_stations(cfg_params)

        # set progress bar
        # with tqdm(total=len(stations), unit='stations') as pbar:
        # iterates over all stations
        for station in stations:
            # get station access token
            station_token = get_station_token(station.id.id)
            # get station attributes
            station_attributes = get_station_attributes(station_token)
            # verify if there is a start date
            if not args.start_date:
                # verify device mostRecentData to define start_date
                # if mostRecentData is empty define start_date to 365 days before today
                if station_attributes['mostRecentData'] == '':
                    start_date = datetime.today() - timedelta(days=365)
                else:
                    start_date = station_attributes['mostRecentData']
            else:
                start_date = args.start_date
            # verify if there is a end date
            if not args.end_date:
                # set today as end_date
                end_date = datetime.today()
            else:
                end_date = args.end_date

            station_data = run_crawler(start_date, end_date, station_attributes['url'])
            load_station_data(station_token, station_data)
                # pbar.set_postfix(current_station=station['stationCode'], refresh=False)
                # pbar.update()

if __name__ == '__main__':
    main()