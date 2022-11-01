import string
import requests
import re
import logging
from time import sleep
import yaml
import os


_LOGGER = logging.getLogger(__name__)

class OrcaApi:
    token = ''
    def __init__(self, username, password, host):
        self.username = username
        self.password = password
        self.host = host
        self.config = self.read_config()

    def test_connection(self):
        url = f'http://{self.host}/cgi/readTags?client=OrcaTouch1172&n=1'
        return self.fetch_data(url, test=True)

    def sensor_status_all(self):
        uri = self.generate_uri(self.config.keys())
        url = f'http://{self.host}{uri}'
        return self.fetch_data(url)

    def sensor_status_by_tag(self, fields: list):
        uri = self.generate_uri(fields)
        url = f'http://{self.host}{uri}'
        return self.fetch_data(url)

    def sensor_status_by_type(self, types: list):
        filtered = { k:v for k,v in self.config.items() if v.get('type') in types }
        uri = self.generate_uri(filtered.keys())
        url = f'http://{self.host}{uri}'
        return self.fetch_data(url)

    def set_value(self, attr, value):
        url = f'http://{self.host}/cgi/writeTags?n=1&t1={attr}&v1={value}'
        return self.fetch_data(url)

    def auth(self):
        try:
            auth_resp = requests.get(f'http://{self.host}/cgi/login?username={self.username}&password={self.password}').text
        except requests.exceptions.ConnectionError as err:
            _LOGGER.warning(f'Could not connect to Orca authentication URL, error: {err}')
            sleep(3)
            return
        if not 'IDALToken' in auth_resp:
            if '#E_TOO_MANY_USERS' in auth_resp:
                _LOGGER.warning(f'Too many users, waiting 60 seconds')
                sleep(60)
                return
            raise Exception(f'Authentication failed. Message from server: {auth_resp}')
        OrcaApi.token = re.search(r'IDALToken=([^\s]+)', auth_resp)[1]
    
    def fetch_data(self, url, test=False):
        cookies = {'IDALToken': OrcaApi.token}
        data_raw = requests.get(url, cookies=cookies).text
        if '#E_NEED_LOGIN' in data_raw:
            self.auth()
            return self.fetch_data(url, test=test)
        if 'E_UNKNOWNTAG' in data_raw and test is True:
            return True
        elif '#E_' in data_raw:
            raise Exception(f'Error while retrieving data. Response: {data_raw}')
        
        return self.parse_data(data_raw)
    
    def parse_data(self, data_raw):
        sensors = []
        splited = data_raw.split('#')
        for sensor_entry in splited:
            success, fields = self.modify_response(sensor_entry)
            if not success:
                continue # TODO handle better
            if fields[1] != 'S_OK':
                continue
            tag = fields[0]
            value = fields[3]
            sensor_config = self.config.get(tag)
            if sensor_config:
                sensors.append(Sensor(tag, sensor_config, reported_value=value))
        return sensors
            
    @staticmethod
    def generate_uri(tags: list) -> string:
        params = ''
        count = 0
        for tag in tags:
            count += 1
            params += f'&t{count}={tag}'
        return f'/cgi/readTags?client=OrcaTouch1172&n={count}{params}'

    @staticmethod
    def modify_response(resp):
        if 'E_UNKNOWNTAG' in resp:
            return False, []
        r = resp.replace('\t',';').replace('\n', ';')
        if not r:
            return False, []
        parsed = r.split(';') # ['2_Temp_VF2', 'S_OK', '192', '217', '']
        if parsed[1] != 'S_OK':
            return False, []
        return True, parsed

    @staticmethod
    def read_config():
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f'{current_dir}/config.yml', mode='r', encoding='utf8') as C:
            config = yaml.safe_load(C)
        if not config:
            raise Exception('nope friend, config was not found')
        return config

class Sensor:
    def __init__(self, tag, sensor_config, reported_value):
        self.tag=tag
        self.name=sensor_config.get('name')
        self.description=sensor_config.get('description'), 
        self.type=sensor_config.get('type')
        self.unit=sensor_config.get('unit')
        self.value_map = sensor_config.get('value_map')
        self.reported_value = self.float_int_check(reported_value)
        self.value = self.find_parser()
        
    def find_parser(self):
        if self.type in ['temperature', 'power_factor']:
            return self.parse_temperature(self.reported_value)
        if self.type in ['boolean']:
            return self.parse_boolean(self.reported_value)
        if self.type in ['multimode']:
            return self.parse_multimode(self.reported_value, self.value_map)

    @staticmethod
    def parse_temperature(value):
        return value/10

    @staticmethod
    def parse_boolean(value):
        if value == 0:
            return False
        if value == 1:
            return True
        return None

    @staticmethod
    def parse_multimode(value, map):
        if not map:
            return value
        return map.get(value, value)

    @staticmethod
    def float_int_check(a):
        try:
            return int(a)
        except ValueError:
            pass
        try:
            return float(a)
        except ValueError:
            pass
        return a
"""
#2_Temp_Zunanja S_OK
192     130
#2_Poti3        S_OK
192     446
#2_Poti4        S_OK
192     433
#2_Temp_Zalog   S_OK
192     -9999
#2_Poti5        S_OK
192     -9999
#2_Vklop_C3     S_OK
192     0
#2_Vklop_ele_grelca_1   S_OK
192     0
#2_Poti1        S_OK
192     245
#2_Izrac_temp_TC        S_OK
192     90
#2_Vklop_C0     S_OK
192     0
#2_Pogoj_maska_pret_stik        S_OK
192     0
#2_Rezim_delov_TC       S_OK
192     0
#2_PRIKAZ_Reg_temp_vode S_OK
192     0
#2_Preklop_PV1  S_OK
192     1
#2_Temp_Prostora        S_OK
192     218
#2_Zahtevana_RF_MK_1    S_OK
192     210
#2_Poti2        S_OK
192     219
#2_Temp_zelena_MK_1     S_OK
192     0
#2_Delovanje_MP1        S_OK
192     0
#2_Odstotki_odprtosti_MP1       S_OK
192     0
#2_Vklop_C1     S_OK
192     0
#2_Temp_RF2     S_OK
192     -9999
#2_Zahtevana_RF_MK_2    S_OK
192     220
#2_Temp_VF2     S_OK
192     218
#2_Temp_zelena_MK_2     S_OK
192     120
#2_Delovanje_MP2        S_OK
192     0
#2_Odstotki_odprtosti_MP2       S_OK
192     0
#2_Vklop_C2     S_OK
192     0
#2_Temp_RF3     S_OK
192     -9999
#2_Zahtevana_RF_DK_3    S_OK
192     220
#2_Izbira_Mitsubishi_Fujitsu    S_OK
192     1
#2_Izbira_mPC_pCO3      S_OK
192     1
#2_Zagon_opravlja_oseba S_OK
192     45
#2_Dan_ZAGONA   S_OK
192     2
#2_Mesec_ZAGONA S_OK
192     6
#2_Leto_ZAGONA  S_OK
192     20
#2_Ura_ZAGONA   S_OK
192     15
#2_Min_ZAGONA   S_OK
192     11
"""