#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
# from tb_inmet_utils import get_api_configuration
from tb_inmet_utils import renew_token
import csv
import json

# read data related to stations metadata
csv_file = open("stations.csv", 'r')
# get API configuration object
# configuration = get_api_configuration(hostname='', username='', password='')
hostname = 'localhost:9090'
username = 'victor@jualabs.com'
password = 'victor'

# create an instance of the API class
device_controller_api_inst = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))

reader = csv.reader(csv_file, delimiter=';')
keys = reader.next()
# iterate over all csv data
for row_of_values in reader:
    current_data = dict(zip(keys, row_of_values))
    # create a device for the current station
    current_device_id = ""
    device_name = current_data['stationCode']
    if(device_name == 'A052'):
        print('debug')
    while True:
        try:
            # saveDevice
            api_response = device_controller_api_inst.get_tenant_device_using_get(device_name)
            #pprint(api_response)
            current_device_id = api_response.id.id
        except ApiException as e:
            if (json.loads(e.body)['message'] == 'Token has expired'):
                renew_token(configuration)
                continue
            else:
                continue
                #print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
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
                continue
                #print("Exception when calling DeviceControllerApi->delete_device_using_delete: %s\n" % e)
        break
csv_file.close()