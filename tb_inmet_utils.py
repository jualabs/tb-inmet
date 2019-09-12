#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json


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