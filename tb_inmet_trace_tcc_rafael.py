#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import calendar
import os
import glob
import csv
import json

# data files root folder
root_path = '/Users/victormedeiros/Downloads/inmet/inmet/data/'
desired_station_code = 'A001'
output_filename = ('inmet-tracing-' + desired_station_code + '.txt')
output_file = open(output_filename,'w')

# iterates over all folders
for folder in os.listdir(root_path):
    current_folder_path = root_path + folder
    # iterates over all '.html' files in one folder
    for input_filename in glob.glob(os.path.join(current_folder_path, '*.html')):
        station_code = input_filename.split('.')[0].split('-')[-1]
        if(station_code != desired_station_code):
            continue
        input_file = open(input_filename, 'r')
        single_str = ''
        for line in input_file:
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
            # 2 - write data to file
            output_file.write(json_str + '\n')
output_file.close()