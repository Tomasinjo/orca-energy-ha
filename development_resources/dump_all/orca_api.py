import string
import requests
import re
import logging
import yaml
import os
import time
from typing import Any, Dict

_LOGGER = logging.getLogger(__name__)

class OrcaApi:
    token = ''
    def __init__(self, username, password, host):
        self.username = username
        self.password = password
        self.host = host
        self.config = None

    def initialize(self):
        self.config = self.read_config()

    def test_connection(self):
        url = f'http://{self.host}/cgi/readTags?client=OrcaTouch1172&n=1'
        self.fetch_data(url, test=True)

    def sensor_status_all(self):
        for uri in self.generate_uri(self.config.keys()):
            url = f'http://{self.host}{uri}'
            self.fetch_data(url)
            time.sleep(1)

    def sensor_status_by_tag(self, fields: list):
        uri = self.generate_uri(fields)[0]
        url = f'http://{self.host}{uri}'
        self.fetch_data(url)

    def set_value(self, attr, value):
        url = f'http://{self.host}/cgi/writeTags?n=1&t1={attr}&v1={value}'
        self.fetch_data(url)

    def auth(self):
        try:
            resp = requests.get(f'http://{self.host}/cgi/login?username={self.username}&password={self.password}')
            auth_resp = resp.text
        except requests.RequestException as err:
            _LOGGER.debug(f'Could not connect to Orca authentication URL, error: {err}')
            time.sleep(3)
            return

        if 'IDALToken' not in auth_resp:
            if '#E_TOO_MANY_USERS' in auth_resp:
                _LOGGER.debug(f'Too many users, waiting 60 seconds')
                time.sleep(60)
                return
            raise Exception(f'Authentication failed. Message from server: {auth_resp}')
        
        OrcaApi.token = re.search(r'IDALToken=([^\s]+)', auth_resp)[1]
    
    def fetch_data(self, url, test=False):
        _LOGGER.debug(f'Fetching data from url {url}')
        cookies = {'IDALToken': OrcaApi.token}
        
        try:
            resp = requests.get(url, cookies=cookies)
            data_raw = resp.text
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return

        if '#E_NEED_LOGIN' in data_raw:
            _LOGGER.debug('Need to authenticate..')
            self.auth()
            self.fetch_data(url, test=test)
            return

        if 'E_UNKNOWNTAG' in data_raw and test is True:
            _LOGGER.debug('unknown tag.')
        elif '#E_' in data_raw:
            print(f'Error while retrieving data. Response: {data_raw}')
    
        print(data_raw)
            
    @staticmethod
    def generate_uri(tags: list) -> list:
        params = ''
        count = 0
        uris = []
        for tag in tags:
            count += 1
            params += f'&t{count}={tag}'
            if count >= 120:
                uris.append(f'/cgi/readTags?client=OrcaTouch1172&n={count}{params}')
                params = ''
                count = 0
        uris.append(f'/cgi/readTags?client=OrcaTouch1172&n={count}{params}')
        return uris

    @staticmethod
    def read_config():
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f'{current_dir}/config.yml', mode='r', encoding='utf8') as C:
            config = yaml.safe_load(C.read())
        if not config:
            raise Exception('nope friend, config was not found')
        return config
