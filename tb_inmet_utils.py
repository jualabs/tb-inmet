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


def renew_token(configuration):
    tokens = get_api_tokens_from_password(configuration.host, configuration.username, configuration.password)
    configuration.api_key['X-Authorization'] = tokens['token']


def get_tb_api_configuration(cfg_params):
    # set configurations values
    # set hostname, username and password from user
    api_cfg = swagger_client.Configuration()
    api_cfg.host = cfg_params['tb_api_access']['host']
    api_cfg.username = cfg_params['tb_api_access']['user']
    api_cfg.password = cfg_params['tb_api_access']['passwd']

    # get tokens
    tokens = get_api_tokens_from_password(api_cfg.host, api_cfg.username, api_cfg.password)
    # configure API key authorization: X-Authorization
    api_cfg.api_key['X-Authorization'] = tokens['token']
    api_cfg.api_key_prefix['X-Authorization'] = 'Bearer'

    return api_cfg