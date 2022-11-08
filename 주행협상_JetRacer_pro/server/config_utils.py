# Copyright 2022 ETRI. All rights reserved. 
# License-identifier: MIT
# kwmin92@etri.re.kr, yssong00@etri.re.kr

""" config """

import json

CONFIG_FILE = 'config_device.json'
def read_device_config():
    """ read config """
    with open(CONFIG_FILE,"r") as jsonFile:
        data = json.load(jsonFile)

    return data['MQTT_SERVER'],data['MQTT_PORT'],data['MQTT_USER'], data['MQTT_PASS']
    
    
