#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
from tb_inmet_utils import load_csv
import ast
import os
import glob

root_path = '/Users/victormedeiros/Downloads/inmet/inmet/data/'

for folder in os.listdir(root_path):
    current_folder_path = root_path + folder
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
        print(data)
        break
    break