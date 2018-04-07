#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import swagger_client

def get_api_tokens_from_password(hostname, username, password):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    data = '{"username":"' + username + '","password":"' + password + '"}'

    response = requests.post('http://' + hostname.strip() + '/api/auth/login', headers=headers, data=data)

    tokens = json.loads(response.content)
    return tokens

def get_api_tokens_from_refresh_token(hostname, tokens):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    data =  '{"grantType":"REFRESH_TOKEN","access_token":"' + tokens['token'] + '","refresh_token":"' + tokens['refreshToken'] + '"}'

    response = requests.post('http://' + hostname.strip() + '/api/auth/token', headers=headers, data=data)

    tokens = json.loads(response.content)
    return tokens

def renew_token(configuration):
    tokens = get_api_tokens_from_password(configuration.host, configuration.username, configuration.password)
    configuration.api_key['X-Authorization'] = tokens['token']

def get_api_configuration(hostname='', username='', password=''):
    # get hostname, username and password from user
    if(hostname == ''):
        hostname = raw_input("please enter hostname: ")
    if (username == ''):
        username = raw_input("please enter username: ")
    if (password == ''):
        password = raw_input("please enter password: ")
    # get tokens
    tokens = get_api_tokens_from_password(hostname, username, password)
    # configure API key authorization: X-Authorization
    configuration = swagger_client.Configuration()
    configuration.host = hostname
    configuration.username = username
    configuration.password = password
    configuration.api_key['X-Authorization'] = tokens['token']
    configuration.api_key_prefix['X-Authorization'] = 'Bearer'

    return configuration