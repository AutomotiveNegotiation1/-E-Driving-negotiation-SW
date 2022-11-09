# Copyright 2022 ETRI. All rights reserved. 
# License-identifier: MIT
# kwmin92@etri.re.kr, yssong00@etri.re.kr

###############################################################################
""" MQTT Client function """
###############################################################################
import paho.mqtt.client as mqtt
from datetime import datetime
#from logging import getLogger, basicConfig, DEBUG, INFO
import json
import random
import time
from config_utils import read_device_config
from function_utils import RingBuffer

MQTT_REPORT_TOPIC = 'report'
MQTT_COMMAND_TOPIC = 'command'
#MQTT_LOC_TOPIC = 'location_car'
MQTT_LOGGING_TOPIC = 'logging' 

import log as logging
LOG = logging.getLogger(__name__)

def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc)) 
    

class Device(object):
    """Represents the state of a single device."""

    def __init__(self, cars_marker_mapping):    
        """ init """
        self.connected = False       
        self.cars_status = {}
        self.car_timeout = 3
        self.cars_marker_mapping = cars_marker_mapping
        self.topic_location_car_timeout = 0
        self.cars_logging = {}
        self.max_log = 100
        
    def wait_for_connection(self, timeout):
        """Wait for the device to become connected."""
        total_time = 0
        while not self.connected and total_time < timeout:
            time.sleep(1)
            total_time += 1

        if not self.connected:
            raise RuntimeError('Could not connect to MQTT bridge.')
            
    def get_car_config_status(self,car_id):
        """ get status """
        if car_id in self.cars_status:
            if 'config' in self.cars_status[car_id]:
                return self.cars_status[car_id]['config']
        return None    
        
    def get_car_report_status(self,car_id):   
        """ get status """
        try:
            if car_id in self.cars_status:
                if 'status' in self.cars_status[car_id]:
                    #print('get_car_report_status',self.cars_status[car_id]['status'])
                    status = self.cars_status[car_id]['status']       
                    try: 
                        connection_time = int(status['connection_time'])
                        current_time = time.time()            
                        if current_time - connection_time > self.car_timeout:
                            connection = "Disconnected"
                            car_status = "Not available"
                            car_location = "Not available"                            
                        else:
                            connection = "Connected"
                            car_status = self.cars_status[car_id]['status']['status']
                            car_location = self.cars_status[car_id]['status']['location']
                            
                    #except Exception as e:
                    except BaseException:
                        LOG.error("Error {}")
                        connection = "Disconnected"
                        car_status = "Not available"
                        car_location = "Not available"
                        
                    self.cars_status[car_id]['status']['connection'] = connection
                    self.cars_status[car_id]['status']['status'] = car_status
                    self.cars_status[car_id]['status']['location'] = car_location
                    #print('=============',self.cars_status[car_id]['status'])
                    return self.cars_status[car_id]['status']
            else:
                car_status = {}
                
                car_status['connection'] = "Disconnected"
                car_status['status'] = "Not available"
                car_status['location'] = "Not available"
                
                return car_status
        #except Exception as e:
        except BaseException:
            LOG.error("Error occurs")
            return None
        return None    
       

    def on_connect(self, unused_client, unused_userdata, unused_flags, rc):
        """Callback for when a device connects."""
        print('Connection Result:', error_str(rc))
        self.connected = True
        
    def on_disconnect(self, unused_client, unused_userdata, rc):
        """Callback for when a device disconnects."""
        print('Disconnected:', error_str(rc))
        self.connected = False

    def on_publish(self, unused_client, unused_userdata, unused_mid):
        """Callback when the device receives a PUBACK from the MQTT bridge."""
        #print('Published message acked.')
        pass

    def on_subscribe(self, unused_client, unused_userdata, unused_mid,
                     granted_qos):
        """Callback when the device receives a SUBACK from the MQTT bridge."""
        print('Subscribed: ', granted_qos)
        if granted_qos[0] == 128:
            print('Subscription failed.')
            
    def topic_report_processing(self, data):
        """ report processing """
        #print(data) 
        car_id = int(data["Car_id"])
        status = data['Status']
        command = data["Command"]
        
        if car_id not in self.cars_status:
            self.cars_status[car_id] = {}
            
        if command == "Status":    
            #connection_time = data["Timestamp"]
            connection_time = time.time()
            
            location = data['Location']
            if 'status' not in self.cars_status[car_id]:
                self.cars_status[car_id]['status'] = {'status':status,
                                                  'connection_time':connection_time,
                                                  'location':location}
            else:
                self.cars_status[car_id]['status'].update({'status':status,
                                                  'connection_time':connection_time,
                                                  'location':location})
        '''                                          
        elif command == "Config" or command == "Remote":
            #print('current cars config status',self.cars_status[car_id])              
            date_time = datetime.fromtimestamp(time.time())
            date_time_str = date_time.strftime("%H:%M:%S, %d/%m/%Y")
            self.cars_status[car_id]['config'] = status + ' ,'+ date_time_str'''
            
        #print('current cars status',self.cars_status[car_id]) 
    '''    
    def topic_loc_processing(self, data):     
    """ location processing """
        
        try:
            car_loc = data["car"]
            
            for marker_id, location_value in car_loc.items():
                marker_id = int(marker_id)                
                if marker_id in self.cars_marker_mapping:
                    car_id = self.cars_marker_mapping[marker_id]                    
                    if car_id not in self.cars_status:
                        self.cars_status[car_id] = {}
                        
                    if 'status' not in self.cars_status[car_id]:    
                        self.cars_status[car_id]['status'] = {"location":location_value}
                    else:
                        self.cars_status[car_id]['status'].update({"location":location_value})
                  
        #except Exception as e:
        except BaseException:
            LOG.error("[topic_loc_processing]")
    '''
    
    def topic_logging_processing(self, data): 
        """ log processing """
        '''
        '{'Car_id': 1, 'marker_id': 8, 'road_type': 1, 'cmd': 7, 'maneuver_type': 2, 
            'remain_distance': 110.13627921806692}'
        '''
        try:
            car_id = data["Car_id"]
            if car_id not in self.cars_status:
                self.cars_status[car_id] = {}
            
            if car_id not in self.cars_logging:
                self.cars_logging[car_id] = RingBuffer(self.max_log)
               
            data_format = '[{} ]{}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data["Logging"])
            self.cars_logging[car_id].append2(data_format) 
            
            log_list = self.cars_logging[car_id].get().copy()    
                        
            self.cars_status[car_id]['config'] = '\n'.join(log_list) 
            #LOG.info(self.cars_status)
        #except Exception as e:
        except BaseException:
            LOG.error("topic_logging_processing ")
            
    def insert_logging_break(self, car_id):   
        """ insert log """
        try:
            data_format = '[{} ]{}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "====================")            
            print("insert to log", data_format)            
            self.cars_logging[car_id].append2(data_format)  
        except IndexError as e:
            print("insert_logging_break error")
            
    def on_message(self, unused_client, unused_userdata, message):
        """Callback when the device receives a message on a subscription."""
        payload = message.payload.decode('utf-8')
        #print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
            #payload, message.topic, str(message.qos)))
        
        if not payload:
            return
        
        data = json.loads(payload)
            
        if message.topic == MQTT_REPORT_TOPIC:
            self.topic_report_processing(data) 
        elif message.topic == MQTT_LOGGING_TOPIC:
            #print("receive topic logging.......................")
            self.topic_logging_processing(data)
        
            

class MQTTClient():    
    """ mqtt client """
    def __init__(self, cars_marker_mapping):        
        """ init """
        self.isrun = False
        self.client = None
        self.device = None    
        self.cars_marker_mapping = cars_marker_mapping
    
    def get_client(self,mqtt_server,mqtt_port,mqtt_user,mqtt_pass):   
        """ get client """
        # Create the MQTT client and connect to Cloud IoT.
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        client = mqtt.Client(client_id=client_id)
        client.username_pw_set(mqtt_user,mqtt_pass)
        
        self.device = Device(self.cars_marker_mapping)

        client.on_connect = self.device.on_connect
        client.on_publish = self.device.on_publish
        client.on_disconnect = self.device.on_disconnect
        client.on_subscribe = self.device.on_subscribe
        client.on_message = self.device.on_message

        try:
            client.connect(mqtt_server, int(mqtt_port))               
            client.loop_start()
        #except Exception as e:
        except BaseException:
            print('Error during connect to server')
            return None
                        
        # Wait up to 5 seconds for the device to connect.
        self.device.wait_for_connection(5)

        # Subscribe to the report topic.
        client.subscribe(MQTT_REPORT_TOPIC, qos=1)   
        client.subscribe(MQTT_LOGGING_TOPIC, qos=1)  
        return client
        

    def setup(self):
        """ setup """
        MQTT_SERVER,MQTT_PORT,MQTT_USER,MQTT_PASS = read_device_config()        
        self.client = self.get_client(MQTT_SERVER,MQTT_PORT,MQTT_USER,MQTT_PASS)        
   
    def set_command(self, payload):
        """ set command """
        #print('connections status:',self.device.connected)
        if not self.device.connected:
            self.setup()
        if self.client is not None:    
            self.client.publish(MQTT_COMMAND_TOPIC, json.dumps(payload), qos=1)         
            
    def insert_logging_break(self, car_id):   
        """ insert log """
        print("insert_logging_break step 1",car_id)
        self.device.insert_logging_break(car_id) 
        
        
    def stop(self):
        """ stop """
        self.client.disconnect()
        self.client.loop_stop()
