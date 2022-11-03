# Copyright 2022 ETRI. All rights reserved. 
# License-identifier: MIT
# kwmin92@etri.re.kr, yssong00@etri.re.kr

###############################################################################
""" auto car """
###############################################################################
import paho.mqtt.client as mqtt

import flask
from flask import Flask, Response, render_template, request, jsonify, flash
#from logging import getLogger, basicConfig, DEBUG, INFO
import json
import time
from my_mqtt_client import MQTTClient
from function_utils import generate_speed
from flask_cors import CORS
import threading

app = Flask(__name__)

CORS(app)

mqtt_client = None
g_cars_running_status = {}
g_cars_list = {1:'Car-A',2:'Car-B',3:'Car-C',4:'Car-D'}
g_cars_marker_mapping = {8:1,2043:2,479:3,4:4}

import log as logging
LOG = logging.getLogger(__name__)

   
DRIVER_MODE = {'Inner Route':'model_road_A.pth',
               'Outer Route':'model_road_B.pth',
               'DriveMode 3':'model_road_C.pth',
               'Manual Mode':'manual'}

SPEED_MODE = None               
               

@app.route('/api/get_drive_mode', methods=['POST'])
def get_drive_mode():   
    """ get mode """
    return jsonify(DRIVER_MODE)     


@app.route('/api/get_speed_value', methods=['POST'])
def get_speed_value():    
    """ set speed """
    return jsonify(SPEED_MODE)            
               
   
@app.route('/api/set_command_run', methods=['POST'])
def set_command_run():    
    """ set run """
    car_id = int(request.json['car_id'])
    command = "Run"
    model = request.json['model']
    speed = request.json['speed']
        
    payload_data = {"Car_id":car_id,
                    "Command": command}
   
    global mqtt_client
    mqtt_client.set_command(payload_data) 
    
    model_text = None
    global g_cars_running_status
       
    for model_key, model_value in DRIVER_MODE.items():
        if model_value == model:
            model_text = model_key
    
    speed_text = None
    for speed_key, speed_value in SPEED_MODE.items():
        if speed_value == speed:
            speed_text = speed_key
            
    if model_text != None and speed_text != None:
        g_cars_running_status[car_id] = ['run',{model_text:model},{speed_text:speed}]        
    
    ret = {"status":True,"message":"OK"}    
    
    return jsonify(ret)
    
 
@app.route('/api/set_command_stop', methods=['POST'])
def set_command_stop():    
    """ set stop """
    car_id = int(request.json['car_id'])
    command = "Stop"
        
    payload_data = {"Car_id":car_id,
                    "Command": command}
    
    global mqtt_client
    mqtt_client.set_command(payload_data) 
    
    global g_cars_running_status
    if car_id in g_cars_running_status:
        g_cars_running_status[car_id][0] = 'stop'
    try:    
        mqtt_client.insert_logging_break(car_id)
    #except Exception as e:
    except BaseException:
        print("exception")
    
    ret = {"status":True,"message":"OK"}    
    return jsonify(ret)
    
    
@app.route('/api/set_command_remote', methods=['POST'])
def set_command_remote():   
    """ set command """
    car_id = int(request.json['car_id'])
    command = "Remote"
    value = request.json['value']
        
    payload_data = {"Car_id":car_id,
                    "Command": command,
                    "Value": value}
    print(payload_data)
    global mqtt_client
    mqtt_client.set_command(payload_data) 
    
    ret = {"status":True,"message":"OK"}    
    return jsonify(ret)   

'''    
@app.route('/api/set_command_status', methods=['POST'])
def set_command_status():    
    """ get status """
    car_id = 0
    command = "Status"
            
    payload_data = {"Car_id":car_id,
                    "Command": command}
                    
    #print(payload_data, time.time())
    global mqtt_client
    mqtt_client.set_command(payload_data) 
    
    ret = {"status":True,"message":"OK"}    
    return jsonify(ret)      
'''    
   
@app.route('/api/get_car_running_status', methods=['POST'])
def get_car_running_status():    
    """ get status """
    car_id = int(request.json['car_id'])
    
    car_status = mqtt_client.device.get_car_report_status(car_id)  
    #print(car_status) 
    if car_status != None:
        if car_status['connection'] == "Disconnected":
            if car_id in g_cars_running_status:
                g_cars_running_status[car_id][0] = 'stop'
    
    if car_id in g_cars_running_status:       
        print('get_car_running_status:',g_cars_running_status[car_id])
        return jsonify(g_cars_running_status[car_id])
    
    return jsonify({})
    
    
@app.route('/api/get_cars_list', methods=['POST'])
def get_cars_list():        
    """ car list """
    return jsonify(g_cars_list)   


@app.route('/api/set_car_scenario', methods=['POST'])
def set_car_scenario():  
    """ set scenario """
    try:
        scenario = request.json['scenario']
        print("scenario",scenario)
        car_id_setting = request.json['car_id_setting']
        print("car_id_setting",car_id_setting)
        global mqtt_client
        
        status = True
        message = "OK"
       
        if scenario == "A" or scenario == "B":  
            car_id = 1 
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}
            mqtt_client.set_command(payload_data) 
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed}
            mqtt_client.set_command(payload_data)

            car_id = 2
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}
            mqtt_client.set_command(payload_data)
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed} 
            mqtt_client.set_command(payload_data)

            car_id = 3
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}       
            mqtt_client.set_command(payload_data) 
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed}
            mqtt_client.set_command(payload_data)
            
        elif scenario == "C":
            car_id = 1
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}
            mqtt_client.set_command(payload_data) 
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed}
            mqtt_client.set_command(payload_data)

            car_id = 3
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}
            mqtt_client.set_command(payload_data) 
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed}
            mqtt_client.set_command(payload_data)
            
        elif scenario == "D":
            car_id = 1
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}
            mqtt_client.set_command(payload_data)
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed}
            mqtt_client.set_command(payload_data)

            car_id = 2
            payload_data = {"Car_id": car_id, "Command": "Scenario", "Class": scenario}
            mqtt_client.set_command(payload_data) 
            model = car_id_setting[str(car_id)]["model"]
            speed = car_id_setting[str(car_id)]["speed"]
            payload_data = {"Car_id": car_id, "Command": "Config", "Model": model, "Speed": speed}
            mqtt_client.set_command(payload_data)
         
        ret = {"status":status,"message":message}    
        LOG.info("payload_data: {}".format(payload_data))
        return jsonify(ret)     
    #except Exception as e:
    except BaseException:
        #LOG.error("Error {}".format(e))
        ret = {"status":False} 
    
'''    
@app.route('/api/get_car_config_status', methods=['POST'])
def get_car_config_status():  
    """ get status """
    car_id = int(request.json['car_id'])
    
    status = True
    car_status = mqtt_client.device.get_car_config_status(car_id)
    if car_status == None:
        status = False
        message = "There is no status"
    else:
        print(car_status)
        message = car_status
    ret = {"status":status,"message":message}    
    return jsonify(ret)    
    

@app.route('/api/get_car_report_status', methods=['POST'])
def get_car_report_status():
    """ get status """
    car_id_list = request.json['car_id_list']
    
    status = True
    car_status_list = []
    
    for car_id in car_id_list:
        car_status = mqtt_client.device.get_car_report_status(int(car_id))   
        if car_status == None:
            status = False
            car_status = "Cannot get car status"
            
        #config_status
        car_config_status = mqtt_client.device.get_car_config_status(int(car_id))
        if car_config_status == None:            
            car_config_status = "There is no status"
        
        car_status_list.append2({'car_id':car_id,'report_status':car_status,'config_status':car_config_status})    
        
    ret = {"status":status,"message":car_status_list}    
    return jsonify(ret)      
'''    
    
@app.route('/api/get_car_overall_status', methods=['POST'])
def get_car_overall_status():    
    """ get status """
    car_id_list = request.json['car_id_list']
    
    status = True
    car_status_list = []
    
    for car_id in car_id_list:
        car_id = int(car_id)
        car_status = mqtt_client.device.get_car_report_status(car_id)  
        #print(car_status) 
        if car_status == None:
            status = False
            car_status = "Cannot get car status"
        elif car_status['connection'] == "Disconnected":
            car_config_status = mqtt_client.device.get_car_config_status(car_id)
            if car_config_status == None:            
                car_config_status = "There is no status"
            if car_id in g_cars_running_status:
                g_cars_running_status[car_id][0] = 'stop'
        else:
            car_config_status = mqtt_client.device.get_car_config_status(car_id)
            if car_config_status == None:            
                car_config_status = "There is no status"
            
        #run/stop status
        
        running_status = {}            
        if car_id in g_cars_running_status:       
            running_status = g_cars_running_status[car_id]
        
        car_status_list.append2({'car_id':car_id,
                                'report_status':car_status,
                                'config_status':car_config_status,
                                'running_status':running_status})    
        
    ret = {"status":status,"message":car_status_list}    
    return jsonify(ret)     


def set_command_status_thread(event_obj):
    """ set command """
    car_id = 0
    command = "Status"
            
    payload_data = {"Car_id":car_id,
                    "Command": command}
                        
    while (not event_obj.is_set()):
        global mqtt_client
        #print('set_command_status_thread',payload_data, time.time())    
        mqtt_client.set_command(payload_data)
        time.sleep(1)
        
        
if __name__ == '__main__':    
    mqtt_client = MQTTClient(g_cars_marker_mapping)
    mqtt_client.setup()
     
    SPEED_MODE = generate_speed()
    
    event_obj = threading.Event()
    x = threading.Thread(target=set_command_status_thread, args=(event_obj,),daemon=True)    
    x.start()
    
    try:
        app.run(host='0.0.0.0', port=50001,threaded=True)
    except KeyboardInterrupt as e:
        event_obj.set()
        mqtt_client.stop()        
    finally:    
        event_obj.set()
        mqtt_client.stop()
    
