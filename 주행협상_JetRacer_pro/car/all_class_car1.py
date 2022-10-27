# Copyright 2022 ETRI. All rights reserved. 
# License-identifier: MIT
# kwmin92@etri.re.kr, yssong00@etri.re.kr


#!/usr/bin/env python
# coding: utf-8

# In[ ]:

""" car1 py """


from jetcam.csi_camera import CSICamera
import ipywidgets
import traitlets
from IPython.display import display
from jetcam.utils import bgr8_to_jpeg

import ipywidgets.widgets as widgets
#import threading

camera = CSICamera(width=224, height=224, capture_fps=20)

image = ipywidgets.Image(format='jpeg')
#display(image)
traitlets.dlink((camera, 'value'), (image, 'value'), transform = bgr8_to_jpeg)
try:
    controller = widgets.Controller(index=0)  # replace with index of your controller
    #display(controller)
except BaseException:
    print("Please insert USB dongle to PC for using Joystick")
    



# Finally, execute the cell below to make the racecar move forward, steering the racecar 
# based on the x value  of the apex.
# 
# Restart camera by command: sudo systemctl restart nvargus-daemon
# 
# Here are some tips:
# 
# * If the car wobbles left and right,  lower the steering gain
# * If the car misses turns,  raise the steering gain
# * If the car tends right, make the steering bias more negative (in small increments like -0.05)
# * If the car tends left, make the steering bias more postive (in small increments +0.05)

# In[ ]:


# This is car 1
import os
import torch
from torch2trt import TRTModule
import ipywidgets.widgets as widgets
from utils import preprocess
import numpy as np
import traitlets
from ar_markers import detect_markers
import time
import paho.mqtt.client as mqtt
import json
from jetracer.nvidia_racecar import NvidiaRacecar
import threading
import math
import time
import serial
import csv
import logging
import socket

from logging.handlers import RotatingFileHandler

log = logging.getLogger(__name__)
handler = RotatingFileHandler("log_all_class.log", mode='w', maxBytes=5*1024*1024,backupCount=2, 
                              encoding=None, delay=0)

handler.setFormatter(logging.Formatter('[%(levelname)s] [%(asctime)s] --- %(lineno)d %(message)s'))

log.addHandler(handler)
log.setLevel(logging.INFO)


#from jetcam.csi_camera import CSICamera
#import ipywidgets

STEERING_GAIN = 0.75
STEERING_BIAS = 0.0

THROTTLE_STD = 0.145

#MQTT_SERVER = '172.16.1.1'
MQTT_SERVER = '192.168.0.197'

# 1 for car1, 2 for car2, ....
CAR_ID = 1
CAR_MARKER_ID = 8

default_mode = 'model_road_A.pth'

ROAD_MAIN = 1
ROAD_RIGHT_FLOW = 2

road_type = ROAD_MAIN
BORDER = 340
SAFE_DISTANCE = 200

ASK_FOR_RIGHT_FLOW = 1
RES_ALLOW_RIGHT_FLOW = 2
RES_NOT_ALLOW_RIGHT_FLOW = 3
ASK_FOR_OVER_TAKING = 4
RES_OK_FOR_OVER_TAKING = 5
DONE_OVER_TAKING = 6
DMM_BROADCAST = 7
RES_OK_FOR_DMM = 8
RES_OK_FOR_PIM = 9
DONE_OVER_RIGHT_FLOW = 10
ASK_FOR_RIGHT_FLOW_E = 11
ASK_FOR_RIGHT_FLOW_E_DONE = 12

DRIVER_STRAIGHT_TYPE = 1
CHANGE_LEFT_LANE_TYPE = 2
CHANGE_RIGHT_LANE_TYPE = 3
OVER_TAKING_TYPE = 4
INTERSECTION_GO_STRAIGHT_TYPE = 5
INTERSECTION_TURN_LEFT_TYPE = 6
INTERSECTION_TURN_RIGHT_TYPE = 7
OTHER_TYPE = 8

STOP = 0
RUN = 1
IN_JUNCTION = 2
OUT_JUNCTION = 3

AUTO_MODE = 0
MANUAL_MODE = 1
RELOAD_MODE = 2

AREA_CHECK = 15

TEST_TOPIC = 'test'
ROAD_INFO_TOPIC = 'road_info'
LOC_TOPIC = 'location_car'
CMD_TOPIC = 'command'
REPORT_TOPIC = 'report'
IMU_TOPIC = 'imu_senseor'
LOGGING_TOPIC = 'logging'

CLASS_A = 0
CLASS_B = 1
CLASS_C = 2
CLASS_D = 3



log.info("Autonomous Car ID:%s",CAR_ID)
log.info("Autonomous Car MarkerID:%s",CAR_MARKER_ID)
log.info("Default model:%s",default_mode)
log.info("Car IP address: %s",(([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
                                 if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), 
                                s.getsockname()[0], s.close()) for s in 
                                [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0])


def get_minvalue(inputlist): 
    """ get min value """
    #get the minimum value in the list
    min_value = min(inputlist)

    #return the index of minimum value 
    res = [i for i,val in enumerate(inputlist) if val==min_value]  

    return res

def get_index_point(rows,x,y): 
    """ get index """
    lst_dist = []
    #Calculate distance for all point
    for i in range(len(rows)):
        #print('get_index_point',i,rows[i])
        car_info = rows[i]
        #print('get_index_point',car_info)
        dist = math.sqrt((int(car_info[1]) - x)**2 + (int(car_info[2]) - y)**2)
        lst_dist.append2(dist)
        
    # Search for minimun element
    min_list = get_minvalue(lst_dist)
    #print(min_list)
    
    ret = []
    if len(min_list) > 0:
        ret = min_list[0]
        #print(rows[min_list[0]],min_list[0])
        
    return ret
    
def closest_point(rows,x,y):
    """ cosest point """
    lst_dist = []
    #Calculate distance for all point
    for i in range(len(rows)):
        #print(i,rows[i])
        car_info = rows[i]
        dist = math.sqrt((int(car_info[1]) - x)**2 + (int(car_info[2]) - y)**2)
        lst_dist.append2(dist)
        
    #print(lst_dist)
    # Search for minimun element
    min_list = get_minvalue(lst_dist)
    #print(min_list)
    
    ret = []
    if len(min_list) > 0:
        ret = rows[min_list[0]]
        #print(rows[min_list[0]],x,y)
        
    return ret

class JoystickController:
    """ joystick """
    def __init__(self,car,controller):    
        """ initalization """
        self.car = car
        self.controller = controller
        left_link = traitlets.dlink((self.controller.axes[0], 'value'), (self.car, 'steering'), 
            transform=lambda x: -x)
        right_link = traitlets.dlink((self.controller.axes[5], 'value'), (self.car, 'throttle'), 
            transform=lambda x: -x)
        print("Joystick is ready now")

class Point(object):
    """ point """
    def __init__(self, x, y):
        """ init """
        self.x, self.y = x, y
        
class ACC_data(object):
    """ acc """
    def __init__(self):
        """ init """
        self.acc_ready = 0
        try:
            self.ser = serial.Serial('/dev/ttyUSB0',115200,timeout=0.001)
            self.acc_ready = 1
        except BaseException:
            print('Can not open device /dev/ttyUSB0')
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
      
        self.dist =0
        self.lasttime = time.time()
        
    def get_quaternion_from_euler(self,roll, pitch, yaw):
        """ get location """
        qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
        qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
        qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
        qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
        return [qx, qy, qz, qw]    
    
    def getData(self):
        """ data """
        try:
            while (self.ser.inWaiting() and (self.acc_ready == 1)):
                rawdata = self.ser.read(2000)
                rawdata = rawdata.split(b'\r\n')
                #print(rawdata)
                imudata = rawdata[0]
                imudata = imudata[1:]
                #print('imudata',imudata)
                data = imudata.decode().split(",")                
                self.dist = math.sqrt( (self.roll - float(data[0]))**2 + (self.pitch - float(data[1]))**2 )
                
                self.roll = float(data[0])                
                self.pitch = float(data[1])                
                self.yaw = float(data[2])
                break
        #except Exception as e:
        except BaseException:
            print('Can not read data from iou sensor')
            pass
            
class Location:
    """ location """
    def __init__(self):
        """ init """
        #self.car = car
        # Initial location
        self.curr_location = Point(0, 0)
        self.prev_location = Point(0, 0)
        #(70,66) ENTRY for road2
        self.entry_junction_location = Point(122, 187)
        # (199, 173) ENTRY for road1
        self.exit_junction_location = Point(55,430)
        self.center_junction_location = Point(40,271)
        self.dist_entry = self.cal_distance(self.curr_location,self.entry_junction_location)
        self.dist_exit  = self.cal_distance(self.curr_location,self.exit_junction_location)
        self.dist_center  = self.cal_distance(self.curr_location,self.center_junction_location)
        self.speed = 0
        self.timestamp = time.time()
        self.update_flag = 0
        
        
    def update_loc(self,new_loc,timestamp):
        """ update """
        
        self.curr_location = new_loc
        self.dist_entry = self.cal_distance(self.curr_location,self.entry_junction_location)
        self.dist_exit  = self.cal_distance(self.curr_location,self.exit_junction_location)
        self.dist_center = self.cal_distance(self.curr_location,self.center_junction_location)
        
        self.dist_speed = self.cal_distance(self.curr_location,self.prev_location)
        speed = self.dist_speed /(10* (timestamp - self.timestamp ))
        self.speed = round((self.speed + speed)/2,2)
        self.timestamp = time.time()
        '''        
        
        self.dist_speed = self.cal_distance(self.curr_location,self.prev_location)        
        self.speed = self.dist_speed /(10* (timestamp - self.timestamp ))
        self.prev_location = self.curr_location
        self.timestamp = timestamp
        print(' Current speed',self.speed)
        self.update_flag = 1
        '''
        
    def cal_distance_travel(self):
        """ get distance """
        dist_travel= self.cal_distance(self.curr_location,self.prev_location)
        self.prev_location = self.curr_location
        return dist_travel
    
    def cal_distance(self,loc1,loc2):
        """ get distance 2 """
        dist = math.sqrt((loc2.x - loc1.x)**2 + (loc2.y - loc1.y)**2)
        return dist
    
    
class Notify(threading.Thread):
    """ notify """
    def __init__(self,car):
        """ init """
        threading.Thread.__init__(self)
        # Lock for wait inital model
        self.ready = 0
        self.default_class = CLASS_A
        #self.camera = CSICamera(width=224, height=224, capture_fps=20)
        self.car_status = "BSM RX"
        self.car = car
        self.location = Location()
        self.imu = ACC_data()
        self.index = 0
        self.other_car_in_junction = 0
        self.mode = AUTO_MODE
        self.running = 1
        
        self.broker = MQTT_SERVER
        self.broker_port = 1883
        self.broker_user = 'netvision'
        self.broker_pass = 'sptqlwus'
        self._mq_reconnect(force=True)
        
        print("Create Model ......")
        self.model_trt = TRTModule()
        self.curr_model = default_mode
        print("Loading pretrained Model ......")
        self.model_trt.load_state_dict(torch.load(self.curr_model))
         
        self.rows = []
        with open("Database.csv", 'r') as file_read:
            csvreader = csv.reader(file_read)
            header = next(csvreader)
            for row in csvreader:
                self.rows.append2(row)   
            
            
        
        # Release for read camera
        self.ready = 1
        self.curr_gas = THROTTLE_STD
        #self.setGas(self.curr_gas)
        self.stopCar()
        self.enable_moving = 0
        
        self.cruise_speed = 0
        self.current_speed = 0
        
        self.cars_infor = []
        self.cars_distance = []
        self.cars_not_same_area = []
        #class A & D
        self.other_car_asked_right_flow = 0
        self.car_right_flow_marker_id = 0
        #class B & C
        self.ask_for_over_taking_flag = 0
        self.enable_over_taking_flag = 0
        self.dmm_marker_id = 0
        
        
        

    def adaptive_cruise_control(self,curr_speed,crui_speed):
        """ control acc """
        delta_gas = 0.004
        if curr_speed > crui_speed:
            gas = self.curr_gas - delta_gas
        elif curr_speed < crui_speed:
            gas = self.curr_gas + delta_gas
        if (gas < 0.17) and (gas > 0.14):    
            self.setGas(gas)
        print('Debug: adaptive_cruise_control',gas)
        #self.setGas(crui_gas)
    
        
    # We can assign values in the range [-1, 1] to these attributes
    def setSteering(self,steering):
        """ set steering """
        self.car.steering = steering
        
    # We can assign values in the range [0, 1] to these attributes    
    def setGas(self,gas):
        """ set throttle """
        self.curr_gas = gas
        self.car.throttle = self.curr_gas
    
    # Stop car by set gas = 0
    def stopCar(self):
        """ stop """
        self.car.throttle = 0
    
    # Restore last gas since it stoped
    def resumeCar(self):
        """ reset car """
        self.car.throttle = self.curr_gas
    
    # Remote Car in 1 second(Manual model)
    def manualControl(self,val):    
        """ control manual """
        if (val == 1):
            steering = -0.5
        elif (val == 2):
            steering = 0
        elif (val == 3):
            steering = 0.5
        print("set steering:",steering)    
        self.setSteering(steering)
        # Enable gas:
        self.resumeCar()
        time.sleep(0.5)
        self.stopCar()
        
    # Reload model if new or change to manual mode
    def setReloadModel(self, model):    
        """ set model """
        if( model == "manual"):
            self.mode = MANUAL_MODE
            self.stopCar()
            print("Changed to Manual Mode")
        elif (model != self.curr_model):
            if not os.path.isfile(model):
                print("Can not find model:",model)
                return
            self.curr_model = model
            self.stopCar()
            self.mode = RELOAD_MODE
            self.model_trt.load_state_dict(torch.load(model))
            self.mode = AUTO_MODE
            print("Reloaded new model",model)
            self.resumeCar()        
        else:
            self.mode = AUTO_MODE
            print("Same with current model",model)
            
    # Process receive message
    def on_mq_message(self, client, userdata, msg):
        """ msg """
        payload = msg.payload.decode("utf-8")
        topic = msg.topic
        
        #print("MQTT topic:",topic,payload)
        if topic == LOC_TOPIC:
            #print("MQTT topic:",topic,payload)
            #MQTT topic: location_car {"car": {"8": [248, 195], "479": [146, 197], "2043": [78, 39]},
            #"obs": {}, "velocity": {"8": 0.0, "479": 0.0, "2043": 0.0}, "timestamp": 1653962577.1484373}

            if not payload:                
                return 0
            data = json.loads(payload)
            car_id = []
            for key in data["car"].keys():
                car_id.append2(int(key))
            #car_id = [8,479,2043] 
            cars_info = []
            for i in range(len(car_id)):
                try:
                    car_info = []            
                    location_data = data["car"][str(car_id[i])]
                    new_loc = Point(location_data[0],location_data[1])
                    if car_id[i] == CAR_MARKER_ID:
                        timestamp = data["timestamp"]
                        self.location.update_loc(new_loc,timestamp)
                    
                    car_info.append2(int(car_id[i]))             # 0: ID
                    car_info.append2(int(location_data[0]))      # 1: X
                    car_info.append2(int(location_data[1]))      # 2: Y 
                    velocity = data["velocity"][str(car_id[i])] # 3: Speed                    
                    car_info.append2(float(velocity))
                    cars_info.append2(car_info)
                    if self.default_class == CLASS_A:
                        self.car_status = "BSM RX"
                #except Exception as e:
                except BaseException:
                    print('No information about location for this car')
            #update other cars_info
            self.cars_info = cars_info
            self.cars_distance = []
            self.cars_not_same_area = []
            numberofcar = len(self.cars_info)
            if numberofcar > 0:# should be  2 cars in main road, we just check 2 cars in main road.                        
                for i in range(numberofcar):
                    if self.cars_info[i][0] == CAR_MARKER_ID:
                        continue
                    car_info = []
                    if (((self.cars_info[i][2] < BORDER) and (self.location.curr_location.y < BORDER)) or 
                    ((self.cars_info[i][2] >= BORDER) and (self.location.curr_location.y >= BORDER))):
                        # Check distance of both car
                        loc1 = Point(self.location.curr_location.x,self.location.curr_location.y)                                                       
                        loc2 = Point(self.cars_info[i][1],self.cars_info[i][2])
                        cars_distance = self.location.cal_distance(loc1,loc2)
                        car_info.append2(self.cars_info[i][0])  # Marker ID
                        car_info.append2(cars_distance)         # Distance
                        car_info.append2(self.cars_info[i][1])  # X 
                        car_info.append2(self.cars_info[i][2])  # Y
                        car_info.append2(self.cars_info[i][3])  # velocity
                        self.cars_distance.append2(car_info)
                        #print("MQTT :",payload,self.cars_info[i][0],self.cars_info[i][3])
                        
                    if (((self.cars_info[i][2] < BORDER) and (self.location.curr_location.y > BORDER)) 
                        or ((self.cars_info[i][2] >= BORDER) and (self.location.curr_location.y < BORDER))):                        
                        self.cars_not_same_area.append2(self.cars_info[i][0])  # Marker ID
                        #print('Add not same area to list',self.cars_not_same_area)
        
        # Broadcast channel 
        if topic == ROAD_INFO_TOPIC: 
            if not payload:                
                return 0
            data = json.loads(payload)                        
            if data["Car_id"] != CAR_ID:
                #print("MQTT topic:",topic,payload)
                #log.info("ROAD_INFO_TOPIC: %s - %s",topic,payload)
                #Check information
                if self.default_class == CLASS_A:
                    if (data["road_type"] == ROAD_RIGHT_FLOW) and (data["cmd"] == ASK_FOR_RIGHT_FLOW):
                        log.info('Get PIM resquest: %s',payload)
                        msg_log = 'Get PIM resquest: {}'.format(payload)
                        self.send_logging(msg_log)
                        self.other_car_asked_right_flow = 1
                        self.car_right_flow_marker_id = int(data["marker_id"])
                        #self.car_status = "PIM RX"
                    pass
                if self.default_class == CLASS_B:
                    if (data["marker_target"] == CAR_MARKER_ID) and (data["cmd"] == RES_OK_FOR_DMM):
                        log.info('Get DMM response: %s',payload)
                        msg_log = 'Get DMM response: {}'.format(payload)
                        self.send_logging(msg_log)
                        self.dmm_marker_id = data["marker_id"]
                        #self.car_status = "DMM RX"
                        self.enable_over_taking_flag = 1
                        if self.car.throttle > 0:
                            # Higher speed to take over
                            self.car.throttle = 0.151
                if self.default_class == CLASS_C: 
                    if (data["marker_target"] == CAR_MARKER_ID) and (data["cmd"] == RES_OK_FOR_OVER_TAKING):
                        log.info('Get DNM Responde Payload: %s',payload)
                        msg_log = 'Get DNM Responde Payload: {}'.format(payload)
                        self.send_logging(msg_log)
                        log.info('DNM_Res SenderID: %s, ReceivedID: %s, AgreementFlag:1', 
                            data["marker_id"],CAR_MARKER_ID )
                        msg_log = ('DNM_Res SenderID: {}, ReceivedID: {}, '
                        'AgreementFlag:1'.format(data["marker_id"],CAR_MARKER_ID))
                        self.send_logging(msg_log)
                        self.enable_over_taking_flag = 1
                        #self.car_status = "DNM RX"
                        if self.car.throttle > 0:
                            # Higher speed to take over
                            #self.car.throttle = 0.155
                            pass
                if self.default_class == CLASS_D:
                    if (data["road_type"] == ROAD_RIGHT_FLOW) and (data["cmd"] == ASK_FOR_RIGHT_FLOW_E):                    
                        if self.other_car_asked_right_flow == 0:
                            if self.other_car_asked_right_flow == 0 :
                                self.car_status = "EDM RX"
                                log.info('Get EDM resquest: %s',payload)
                                msg_log = 'Get EDM resquest: {}'.format(payload)
                                self.send_logging(msg_log)
                            self.other_car_asked_right_flow = 1
                            self.car_right_flow_marker_id = int(data["marker_id"])
                    elif (data["road_type"] == ROAD_RIGHT_FLOW) and (data["cmd"] == ASK_FOR_RIGHT_FLOW_E_DONE):
                        self.other_car_asked_right_flow = 0
                        log.info('Get EDM done: %s',payload)
                        msg_log = 'Get EDM done: {}'.format(payload)
                        self.send_logging(msg_log)
                        self.car_status = "BSM RX"
                        if self.car.throttle == 0:
                            log.info('Resume car when congesstion request done')
                            self.resumeCar()
                            
        if topic == TEST_TOPIC: 
            if not payload:                
                return 0
            data = json.loads(payload)
            pass
            
                        
        if topic == CMD_TOPIC: 
            if not payload:                
                return 0
            data = json.loads(payload)
            if data["Car_id"] == CAR_ID:
                log.info("MQTT CMD_TOPIC topic: %s",payload) 
                #{"Car_id": 1, "Command": "Scenario", "Class": "C" }
                if (data["Command"] == "Scenario"):
                    if (data["Class"] == "A"):
                        self.default_class = CLASS_A
                        self.location.entry_junction_location = Point(122, 187)
                        self.location.exit_junction_location = Point(55,430)
                        self.location.center_junction_location = Point(42,258)
                    elif (data["Class"] == "B"):
                        self.default_class = CLASS_B
                        self.location.entry_junction_location = Point(122, 187)
                        self.location.exit_junction_location = Point(55,430)
                        self.location.center_junction_location = Point(42,258)
                    elif (data["Class"] == "C"):
                        self.default_class = CLASS_C
                        self.location.entry_junction_location = Point(122, 187)
                        self.location.exit_junction_location = Point(55,430)
                        self.location.center_junction_location = Point(42,258)
                    elif (data["Class"] == "D"):
                        self.default_class = CLASS_D
                        self.location.entry_junction_location = Point(226, 194)
                        self.location.exit_junction_location = Point(55,430)
                        self.location.center_junction_location = Point(6,258)
                
                #{"car_id": 1, "Command": "Config", "Model": "model_road_A.pth" , "Speed": 0.145 }
                if (data["Command"] == "Config"):
                    model = data["Model"]
                    gas = data["Speed"]
                    print("Command config:",model,gas)
                    jsondata = {
                        "Car_id": CAR_ID,
                        "Command": "Config",
                        "Status": "OK"
                    }                   
                    self.send_report(json.dumps(jsondata))                    
                    print("Set gas to:",gas)
                    self.curr_gas = gas                    
                    self.setReloadModel(model)
                    #self.enable_moving = 0
                    
                    
                #{"car_id": 1, "Command": "Run"}
                if (data["Command"] == "Run"):
                    print("Start Car")
                    self.enable_moving = 1
                    self.resumeCar()
                    jsondata = {
                        "Car_id": CAR_ID,
                        "Command": "Run",
                        "Status": "OK"
                    }                   
                    self.send_report(json.dumps(jsondata))
                    
                #{"car_id": 1, "Command": "Stop"}
                if (data["Command"] == "Stop"):
                    print("Stop Car")
                    self.enable_moving = 0
                    self.stopCar()
                    jsondata = {
                        "Car_id": CAR_ID,
                        "Command": "Stop",
                        "Status": "OK"
                    }                   
                    self.send_report(json.dumps(jsondata))
                    
                #{"car_id": 1, "Command": "Remote", "Value": 1}
                if (data["Command"] == "Remote"):
                    #Do nothing right now
                    val = data["Value"]
                    status = "NOK"
                    if( self.mode == MANUAL_MODE):
                        status = "OK"                 
                        
                    #{"car_id": 1, "Command": "Remote", "Status": "OK"}
                    jsondata = {
                        "Car_id": CAR_ID,
                        "Command": "Remote",
                        "Status": status
                    }                   
                    self.send_report(json.dumps(jsondata))
                    print("Received cmd for remote")
                    if( self.mode == MANUAL_MODE):
                        self.manualControl(val)
            elif data["Car_id"] == 0:
                #{"car_id": 1, “Connection”: “Connected”,  “Status": “Idle”,   “Location": “IX-Entrance”}
                #print(data)
                if (data["Command"] == "Status"):
                    location = "{}, {}".format(self.location.curr_location.x,self.location.curr_location.y)                  
                    jsondata = {
                        "Car_id": CAR_ID,
                        "Command": "Status",
                        "Timestamp": time.time(),
                        "Status": self.car_status,
                        "Location": location
                    }                   
                    self.send_report(json.dumps(jsondata))
                    
    def on_disconnect(self, client, userdata, rc):
        """ disconnect """
        print("Disconect happended, re-connect with server now ...")
        self._mq_reconnect(force=True)
    
    def on_mq_connect(self, client, userdata, flags, rc):
        """ connect """
        self.mq_client.subscribe(TEST_TOPIC)
        self.mq_client.subscribe(CMD_TOPIC)
        self.mq_client.subscribe(LOC_TOPIC)
        self.mq_client.subscribe(ROAD_INFO_TOPIC)
        

    def notify(self,msg):
        """ notify """
        if self.enable_moving == 1:
            self._mq_reconnect()
            #print("sending message to: {0} payload: {1}".format(TEST_TOPIC, msg))
            self.mq_client.publish(TEST_TOPIC, msg)
        
    def send_road_info(self,msg):
        """ road info """
        if self.enable_moving == 1:
            self._mq_reconnect()
            self.mq_client.publish(ROAD_INFO_TOPIC, msg)
        
    def send_logging(self,msg):
        """ log """
        self._mq_reconnect()
        jsondata = {
            "Car_id": CAR_ID,
            "Logging":msg
        }
        self.mq_client.publish(LOGGING_TOPIC, json.dumps(jsondata))
        
    def update_imu(self,msg):
        """ update imu """
        self._mq_reconnect()
        #print("sending message to: {0} payload: {1}".format(TEST_TOPIC, msg))
        self.mq_client.publish(IMU_TOPIC , msg)    
    
    def send_report(self,msg):
        """ report """
        #print(" ================>>>>>> command !")
        self._mq_reconnect()
        #print("sending message to: {0} payload: {1}".format(CMD_TOPIC, msg))
        self.mq_client.publish(REPORT_TOPIC, msg)
    
    def _mq_reconnect(self, force=False):
        """ reconnect """
        if force:
            self.mq_connected = False
        while not self.mq_connected:
            try:
                self.mq_client = mqtt.Client()
                self.mq_client.username_pw_set(self.broker_user, password=self.broker_pass)
                self.mq_client.on_connect = self.on_mq_connect
                self.mq_client.on_disconnect = self.on_disconnect
                self.mq_client.on_message = self.on_mq_message
                self.mq_client.connect(host=self.broker,port=self.broker_port)
                self.mq_client.loop_start()
                self.mq_connected = True
                print("Connected to MQTT server!")
            #except Exception as ex:
            except BaseException:
                #print("Could not connect to MQ: {0}".format(ex))
                print("Trying again in 5 seconds...")
                time.sleep(5)
    
    def stop(self):
        """ stop """
        self.running = 0
        self.stopCar()
        camera.cap.release()
        
    def search_in_dlist(self,dlist,marker):
        """ distance  """
        for i in range(len(dlist)):
            if dlist[i][0] == marker:
                return dlist[i]
            
        return []
        
            
    def run(self):
        """ run """
        last_send_broadcast = 0
          
        while (self.ready == 0):
            time.sleep(1)
            
        print("Ready!")
        prv_time = time.time()
        
        lasttime_bsm = time.time()
        close_stopped = []
        # Variable for class A
        C_Veh_marker = 0        
        # Variable for class B
        over_taking_step = 0
        remain_distance = 0
        # Variable for class C        
        receiver_marker_id = 0
        # Variable for class D
        stopped_flag = 0
        while True:
            if self.running == 0:                
                print("Quit ...")
                break
            #Check mode
            if (self.mode == MANUAL_MODE):
                time.sleep(1)
                continue
            if self.default_class == CLASS_A:
                if self.other_car_asked_right_flow == 1:
                    number_cars = len(self.cars_info)               
                    if number_cars > 0:                    
                        cars_distance = []
                        for i in range(number_cars):
                            distance = []
                            loc = Point(self.cars_info[i][1],self.cars_info[i][2])
                            dst = self.location.cal_distance(self.location.center_junction_location,loc)                           
                            distance.append2(self.cars_info[i][0])  # Marker ID
                            distance.append2(dst)                   # Distance
                            distance.append2(self.cars_info[i][1])  # X 
                            distance.append2(self.cars_info[i][2])  # Y
                            cars_distance.append2(distance)
                            #print(self.cars_info[i][0],distance)
                            if ((self.cars_info[i][0] != CAR_MARKER_ID) and 
                                (self.cars_info[i][0] != self.car_right_flow_marker_id)):
                                C_Veh_marker = self.cars_info[i][0]
                                #print('C_Veh_marker',C_Veh_marker)
                    if C_Veh_marker != 0:
                        C_Veh = self.search_in_dlist(cars_distance,C_Veh_marker)
                        #print(C_Veh)
                        try:
                            if C_Veh[3] < BORDER:
                                if C_Veh[2] < self.location.center_junction_location.x: #already pass center junction
                                    if self.location.dist_center > SAFE_DISTANCE:                                
                                        print('You can go now')
                                        self.other_car_asked_right_flow = 0
                                        last_send_broadcast = 0
                                        jsondata = {
                                            "Car_id": CAR_ID,
                                            "marker_id":self.car_right_flow_marker_id,
                                            "road_type": road_type,
                                            "cmd": RES_ALLOW_RIGHT_FLOW
                                        }
                                        self.send_road_info(json.dumps(jsondata))
                                        log.info('Send PIM respond: %s', jsondata)
                                        msg_log = 'Send PIM respond: {}'.format(jsondata)
                                        self.send_logging(msg_log)
                                        #self.car_status = "PIM RX"
                                    else:
                                        if last_send_broadcast == 0:
                                            last_send_broadcast = 1
                                            print('You must wait until I pass to center of junction')
                                        jsondata = {
                                            "Car_id": CAR_ID,
                                            "marker_id":self.car_right_flow_marker_id,
                                            "road_type": road_type,
                                            "cmd": RES_NOT_ALLOW_RIGHT_FLOW
                                        }
                                        self.send_road_info(json.dumps(jsondata))
                                        log.info('Send PIM respond : %s', jsondata)
                                        msg_log = 'Send PIM respond NOT_ALLOW_RIGHT_FLOW: {}'.format(jsondata)
                                        self.send_logging(msg_log)
                                        #self.car_status = "PIM RX"
                                else: # Not yet come to center of junction
                                    # check C_Veh distance
                                    if C_Veh[1] > SAFE_DISTANCE :
                                        print('You can go now')
                                        self.other_car_asked_right_flow = 0
                                        last_send_broadcast = 0
                                        jsondata = {
                                            "Car_id": CAR_ID,
                                            "marker_id":self.car_right_flow_marker_id,
                                            "road_type": road_type,
                                            "cmd": RES_ALLOW_RIGHT_FLOW
                                        }
                                        self.send_road_info(json.dumps(jsondata))
                                        log.info('Send PIM respond : %s', jsondata)
                                        msg_log = 'Send PIM respond RES_ALLOW_RIGHT_FLOW: {}'.format(jsondata)
                                        self.send_logging(msg_log)
                                        #self.car_status = "PIM TX"
                                    else:
                                        if last_send_broadcast == 0:
                                            print('You must wait until I pass to center of junction and '
                                           ' C-Veh2 distance >  SAFE_DISTANCE')
                                            last_send_broadcast = 1
                                        jsondata = {
                                            "Car_id": CAR_ID,
                                            "marker_id":self.car_right_flow_marker_id,
                                            "road_type": road_type,
                                            "cmd": RES_NOT_ALLOW_RIGHT_FLOW
                                        }
                                        self.send_road_info(json.dumps(jsondata))
                                        log.info('Send PIM respond : %s', jsondata)
                                        msg_log = 'Send PIM respond NOT_ALLOW_RIGHT_FLOW: {}'.format(jsondata)
                                        self.send_logging(msg_log)
                                        #self.car_status = "PIM RX"
                            else:
                                if self.location.dist_center > SAFE_DISTANCE:
                                    print('C_Veh1 in other part, You can go now',self.location.dist_center)
                                    self.other_car_asked_right_flow = 0
                                    jsondata = {
                                        "Car_id": CAR_ID,
                                        "marker_id":self.car_right_flow_marker_id,
                                        "road_type": road_type,
                                        "cmd": RES_ALLOW_RIGHT_FLOW
                                    }
                                    self.send_road_info(json.dumps(jsondata))
                                    log.info('Send PIM respond : %s', jsondata)
                                    msg_log = 'Send PIM respond RES_ALLOW_RIGHT_FLOW: {}'.format(jsondata)
                                    self.send_logging(msg_log)
                                    #self.car_status = "PIM RX"
                                else:
                                    if last_send_broadcast == 0:
                                        print('C_Veh1 in other part but, you must wait '
                                        'until I pass to center of junction', self.location.dist_center)
                                        last_send_broadcast = 1
                                    jsondata = {
                                            "Car_id": CAR_ID,
                                            "marker_id":self.car_right_flow_marker_id,
                                            "road_type": road_type,
                                            "cmd": RES_NOT_ALLOW_RIGHT_FLOW
                                    }
                                    self.send_road_info(json.dumps(jsondata))
                                    log.info('Send PIM respond : %s', jsondata)
                                    msg_log = 'Send PIM respond NOT_ALLOW_RIGHT_FLOW: {}'.format(jsondata)
                                    self.send_logging(msg_log)
                                    #self.car_status = "PIM RX"
                        except BaseException:
                            print('Errors when read',C_Veh)
                            pass


                # Check car in case not same part, but in closed_list
                number_cars = len(self.cars_not_same_area)
                if number_cars > 0:
                    for i in range(number_cars):                    
                        try:
                            #print('Debug',self.cars_not_same_area[i],close_stopped)
                            if self.cars_not_same_area[i] in close_stopped:
                                close_stopped.remove(self.cars_not_same_area[i])
                                print("Remove from list close_stopped because not same area", 
                                    self.cars_not_same_area[i])
                        except BaseException:
                            pass
                number_cars = len(self.cars_distance)               
                if number_cars > 0:
                    for i in range(number_cars):   
                        if self.cars_distance[i][1] < SAFE_DISTANCE:
                            if self.location.curr_location.y <  BORDER: 
                                if self.location.curr_location.x > self.cars_distance[i][2]:                                
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        index = get_index_point(self.rows,self.cars_distance[i][2], 
                                            self.cars_distance[i][3])
                                        #print(self.rows[index])
                                        loc1 = Point(self.cars_distance[i][2],self.cars_distance[i][3])
                                        loc2 = Point(int(self.rows[index][1]),int(self.rows[index][2]))
                                        dst = self.location.cal_distance(loc1,loc2)
                                        #print('dst',dst)
                                        if dst < 80:
                                            close_stopped.append2(self.cars_distance[i][0]) 
                                            print("This car is behind other car",self.cars_distance[i][0], 
                                                self.cars_distance[i][1], self.cars_distance[i][4])


                            else: #in upper part, higher than BORDER
                                if self.location.curr_location.x < self.cars_distance[i][2]:
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        close_stopped.append2(self.cars_distance[i][0])
                                        print("This car is behind other car",self.cars_distance[i][0], 
                                            self.cars_distance[i][1], self.cars_distance[i][4])

                        else:
                            if self.cars_distance[i][0] in close_stopped:
                                close_stopped.remove(self.cars_distance[i][0])
                                print("Remove from list close_stopped because safe distance", 
                                    self.cars_distance[i][0],self.cars_distance[i][1], self.cars_distance[i][4])


                image = camera.read() # alway read camera for last frame ???          

                image = preprocess(image).half()
                output = self.model_trt(image).detach().cpu().numpy().flatten()
                x = float(output[0])
                self.car.steering = x * STEERING_GAIN + STEERING_BIAS                      
                if self.enable_moving == 1:
                    if len(close_stopped) > 0:
                        if self.car.throttle > 0:
                            print('stop car',close_stopped)
                            self.stopCar()
                    else:
                        if (self.car.throttle == 0) and self.mode == AUTO_MODE:
                            print('Resume car')
                            self.resumeCar()
                else:
                    if self.car.throttle > 0:
                        self.car.throttle = 0
                    
                continue
            if self.default_class == CLASS_B:
                # Check car in case not same part, but in closed_list
                number_cars = len(self.cars_not_same_area)
                if number_cars > 0:
                    for i in range(number_cars):                    
                        try:
                            #print('Debug',self.cars_not_same_area[i],close_stopped)
                            if self.cars_not_same_area[i] in close_stopped:
                                pass
                                #close_stopped.remove(self.cars_not_same_area[i])
                                #log.debug("Remove from list close_stopped because not same area 
                                #%s",self.cars_not_same_area[i])
                        except BaseException:
                            pass
                number_cars = len(self.cars_distance)               
                if number_cars > 0:
                    for i in range(number_cars):   
                        if self.cars_distance[i][1] < SAFE_DISTANCE:
                            remain_distance = self.cars_distance[i][1]
                            if self.location.curr_location.y <  BORDER: 
                                if self.location.curr_location.x > self.cars_distance[i][2]:                                
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        index = get_index_point(self.rows,self.cars_distance[i][2],
                                            self.cars_distance[i][3])
                                        #print(self.rows[index])
                                        loc1 = Point(self.cars_distance[i][2],self.cars_distance[i][3])
                                        loc2 = Point(int(self.rows[index][1]),int(self.rows[index][2]))
                                        dst = self.location.cal_distance(loc1,loc2)
                                        #print('dst',dst)
                                        if dst < 80:
                                            close_stopped.append2(self.cars_distance[i][0])                                          
                                            log.debug("This car is behind other car %s %s %s", 
                                                self.cars_distance[i][0], 
                                                self.cars_distance[i][1], self.cars_distance[i][4])


                            else: #in upper part, higher than BORDER
                                if self.location.curr_location.x < self.cars_distance[i][2]:
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        close_stopped.append2(self.cars_distance[i][0])
                                        log.debug("This car is behind other car %s %s %s", 
                                            self.cars_distance[i][0],self.cars_distance[i][1], 
                                            self.cars_distance[i][4])

                        else:
                            if self.cars_distance[i][0] in close_stopped:
                                close_stopped.remove(self.cars_distance[i][0])
                                log.debug("Remove from list close_stopped because safe distance %s %s %s", 
                                    self.cars_distance[i][0],self.cars_distance[i][1], self.cars_distance[i][4])


                image = camera.read() # alway read camera for last frame ???          

                image = preprocess(image).half()
                output = self.model_trt(image).detach().cpu().numpy().flatten()
                x = float(output[0])
                steering = x * STEERING_GAIN + STEERING_BIAS 


                if (self.enable_over_taking_flag == 1) and (self.enable_moving == 1):
                    self.car.steering = steering + 0.2 
                    #if len(close_stopped) == 0:
                    if self.dmm_marker_id not in close_stopped:
                        self.enable_over_taking_flag = 0
                        if self.car.throttle > 0:
                            # Back to normal speed
                            self.car.throttle = 0.15
                            pass

                        self.ask_for_over_taking_flag = 0                    
                        jsondata = {
                            "Car_id": CAR_ID,
                            "marker_id":CAR_MARKER_ID,
                            "marker_target": self.dmm_marker_id,
                            "cmd": DONE_OVER_TAKING
                        }
                        log.info('Send DMM Done!: %s',jsondata)
                        self.send_road_info(json.dumps(jsondata)) 
                        msg_log = 'Send DMM Done: {}'.format(jsondata)
                        self.send_logging(msg_log)
                        self.car_status = "BSM RX"

                else:
                    self.car.steering = steering


                if self.enable_moving == 1:
                    if len(close_stopped) > 0:
                        if self.car.throttle > 0:
                            # Slow to wait reply
                            self.car.throttle = 0.15
                            if self.ask_for_over_taking_flag == 0:
                                # Ask permission to over taking
                                jsondata = {
                                    "Car_id": CAR_ID,
                                    "marker_id":CAR_MARKER_ID,
                                    "road_type": road_type,
                                    "cmd": DMM_BROADCAST,
                                    "maneuver_type":CHANGE_LEFT_LANE_TYPE,
                                    "remain_distance":remain_distance
                                }
                                self.send_road_info(json.dumps(jsondata))
                                self.ask_for_over_taking_flag = 1
                                self.enable_over_taking_flag = 0
                                log.info('Send Request for DMM: %s',jsondata)
                                msg_log = 'Send Request for DMM: {}'.format(jsondata)
                                self.send_logging(msg_log)
                                log.info('Send DMM notification: Maneuver type %s, Remain Distance: %s'
                                         , CHANGE_LEFT_LANE_TYPE, remain_distance)
                                msg_log = ('Send DMM notification: Maneuver type {},'
                                'Remain Distance: {}'.format(CHANGE_LEFT_LANE_TYPE, remain_distance))
                                self.send_logging(msg_log)
                                self.car_status = "DMM TX"

                    else:
                        if (self.car.throttle == 0) and self.mode == AUTO_MODE:
                            log.info('Resume car')
                            self.resumeCar()
                else:
                    if self.car.throttle > 0:
                        self.car.throttle = 0
                continue
                
            if self.default_class == CLASS_C:
                # Check car in case not same part, but in closed_list
                number_cars = len(self.cars_not_same_area)
                if number_cars > 0:
                    for i in range(number_cars):                    
                        try:
                            #print('Debug',self.cars_not_same_area[i],close_stopped)
                            if self.cars_not_same_area[i] in close_stopped:
                                #pass
                                close_stopped.remove(self.cars_not_same_area[i])
                                #log.info("Remove from list close_stopped because not same area %s", 
                                #self.cars_not_same_area[i])
                        except BaseException:
                            pass
                number_cars = len(self.cars_distance)               
                if number_cars > 0:
                    for i in range(number_cars):   
                        if self.cars_distance[i][1] < SAFE_DISTANCE:
                            remain_distance = self.cars_distance[i][1]
                            receiver_marker_id = self.cars_distance[i][0]
                            if self.location.curr_location.y <  BORDER: 
                                if self.location.curr_location.x > self.cars_distance[i][2]:                                
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        index = get_index_point(self.rows,self.cars_distance[i][2],
                                            self.cars_distance[i][3])
                                        #print(self.rows[index])
                                        loc1 = Point(self.cars_distance[i][2],self.cars_distance[i][3])
                                        loc2 = Point(int(self.rows[index][1]),int(self.rows[index][2]))
                                        dst = self.location.cal_distance(loc1,loc2)
                                        #print('dst',dst)
                                        if dst < 80:
                                            close_stopped.append2(self.cars_distance[i][0]) 
                                            log.info("This car is behind other car %s %s %s", 
                                                self.cars_distance[i][0],self.cars_distance[i][1],
                                                self.cars_distance[i][4])


                            else: #in upper part, higher than BORDER
                                if self.location.curr_location.x < self.cars_distance[i][2]:
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        close_stopped.append2(self.cars_distance[i][0])
                                        #log.info("This car is behind other car %s %s %s",
                                        #self.cars_distance[i][0],self.cars_distance[i][1], 
                                        #self.cars_distance[i][4])

                        else:
                            if self.cars_distance[i][0] in close_stopped:
                                close_stopped.remove(self.cars_distance[i][0])
                                #log.info("Remove from list close_stopped because safe distance %s %s %s", 
                                #self.cars_distance[i][0],self.cars_distance[i][1], self.cars_distance[i][4])


                image = camera.read() # alway read camera for last frame ???          

                image = preprocess(image).half()
                output = self.model_trt(image).detach().cpu().numpy().flatten()
                x = float(output[0])
                steering = x * STEERING_GAIN + STEERING_BIAS 


                if (self.enable_over_taking_flag == 1) and (self.enable_moving == 1):
                    self.car.steering = steering + 0.258 

                    if len(close_stopped) == 0:
                        self.enable_over_taking_flag = 0
                        if self.car.throttle > 0:
                            # Back to normal speed
                            #self.car.throttle = 0.152
                            pass
                        self.ask_for_over_taking_flag = 0

                        jsondata = {
                            "Car_id": CAR_ID,
                            "marker_id":CAR_MARKER_ID,
                            "receiver_marker_id":receiver_marker_id,
                            "road_type": road_type,
                            "cmd": DONE_OVER_TAKING
                        }
                        self.send_road_info(json.dumps(jsondata)) 
                        log.info('Send DNM_Done payload!: %s',jsondata)
                        msg_log = 'Send DNM_Done done payload: {}'.format(jsondata)
                        self.send_logging(msg_log)
                        log.info('DNM_Done: SenderID: %s, ReceiverID: %s, '
                        'NegoDrivingDone : Done',CAR_MARKER_ID,receiver_marker_id)
                        msg_log = ('DNM_Done: SenderID: {}, ReceiverID: {}, '
                        'NegoDrivingDone : Done'.format(CAR_MARKER_ID,receiver_marker_id))
                        self.send_logging(msg_log)
                        self.car_status = "BSM RX"
                else:
                    self.car.steering = steering

                if self.enable_moving == 1:
                    if len(close_stopped) > 0:
                        if self.car.throttle > 0:
                            # Slow to wait reply
                            #self.car.throttle = 0.15
                            if self.ask_for_over_taking_flag == 0:
                                # Ask permission to over taking
                                jsondata = {
                                    "Car_id": CAR_ID,
                                    "marker_id":CAR_MARKER_ID,
                                    "receiver_marker_id":receiver_marker_id,
                                    "road_type": road_type,
                                    "cmd": ASK_FOR_OVER_TAKING,
                                    "remain_distance":remain_distance
                                }
                                self.send_road_info(json.dumps(jsondata))
                                self.ask_for_over_taking_flag = 1
                                self.enable_over_taking_flag = 0
                                log.info('Send DNM_Req for over taking %s',jsondata)
                                msg_log = 'Send DNM_Req for over taking: {}'.format(jsondata)
                                self.send_logging(msg_log)
                                log.info('DNM_Req: SenderID: %s, '
                                         'ReceiverID: %s, Remain Distance: %s',CAR_MARKER_ID,
                                         receiver_marker_id,remain_distance) 
                                msg_log = ( 'DNM_Req: SenderID: {}, ReceiverID: {} '
                                ',Remain Distance: {}'.format(CAR_MARKER_ID,receiver_marker_id,remain_distance))
                                self.send_logging(msg_log)
                                self.car_status = "DNM REQ"
                    else:
                        if (self.car.throttle == 0) and self.mode == AUTO_MODE:
                            log.info('Resume car')
                            self.resumeCar()
                else:
                    if self.car.throttle > 0:
                        self.car.throttle = 0
                continue
                
            if self.default_class == CLASS_D:
                if self.other_car_asked_right_flow == 1:
                    # In other part
                    if self.location.curr_location.y > self.location.center_junction_location.y: 
                        #print("I am in other part")
                        self.other_car_asked_right_flow = 0
                        last_send_broadcast = 0
                        jsondata = {
                            "Car_id": CAR_ID,
                            "marker_id":self.car_right_flow_marker_id,
                            "road_type": road_type,
                            "cmd": RES_ALLOW_RIGHT_FLOW
                        }
                        self.send_road_info(json.dumps(jsondata))
                        
                    else: # Same part
                        if stopped_flag == 0:                        
                            stopped_flag = 1
                            jsondata = {
                                "Car_id": CAR_ID,
                                "marker_id":self.car_right_flow_marker_id,
                                "road_type": road_type,
                                "cmd": RES_ALLOW_RIGHT_FLOW
                            }
                            self.send_road_info(json.dumps(jsondata))
                            log.info('Send EDM_Res for Concession %s',jsondata)
                            msg_log = 'Send EDM_Res for Concession: {}'.format(jsondata)
                            self.send_logging(msg_log)
                            self.car_status = "EDM RX"
                        if (self.location.dist_entry < 2*AREA_CHECK) and (stopped_flag == 1):
                            stopped_flag = 0
                            if self.car.throttle > 0:
                                self.car.throttle = 0
                            #self.car_status = "Stopped"
                            log.info('Stopped because of request for Concession')
                            msg_log = 'Stopped because of request for Concession'
                            self.send_logging(msg_log)
                if self.enable_moving == 1:
                    if len(close_stopped) > 0:
                        if self.car.throttle > 0:
                            print('stop car',close_stopped)
                            self.stopCar()
                    else:
                        if (self.car.throttle == 0) and self.mode == AUTO_MODE:
                            if self.other_car_asked_right_flow == 0:
                                print('Resume car')
                                self.resumeCar()
                else:
                    if self.car.throttle > 0:
                        self.car.throttle = 0
                    continue


                # Check car in case not same part, but in closed_list
                number_cars = len(self.cars_not_same_area)
                if number_cars > 0:
                    for i in range(number_cars):                    
                        try:
                            #print('Debug',self.cars_not_same_area[i],close_stopped)
                            if self.cars_not_same_area[i] in close_stopped:
                                close_stopped.remove(self.cars_not_same_area[i])
                                print("Remove from list close_stopped because not same area", 
                                    self.cars_not_same_area[i])
                        except BaseException:
                            pass
                number_cars = len(self.cars_distance)               
                if number_cars > 0:
                    for i in range(number_cars):   
                        if self.cars_distance[i][1] < SAFE_DISTANCE:
                            if self.location.curr_location.y <  BORDER: 
                                if self.location.curr_location.x > self.cars_distance[i][2]:                                
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        index = get_index_point(self.rows,self.cars_distance[i][2], 
                                            self.cars_distance[i][3])
                                        #print(self.rows[index])
                                        loc1 = Point(self.cars_distance[i][2],self.cars_distance[i][3])
                                        loc2 = Point(int(self.rows[index][1]),int(self.rows[index][2]))
                                        dst = self.location.cal_distance(loc1,loc2)
                                        #print('dst',dst)
                                        if dst < 80:
                                            close_stopped.append2(self.cars_distance[i][0]) 
                                            print("This car is behind other car",self.cars_distance[i][0],
                                                self.cars_distance[i][1], self.cars_distance[i][4])


                            else: #in upper part, higher than BORDER
                                if self.location.curr_location.x < self.cars_distance[i][2]:
                                    if (self.cars_distance[i][0] not in close_stopped):
                                        close_stopped.append2(self.cars_distance[i][0])
                                        print("This car is behind other car",self.cars_distance[i][0],
                                            self.cars_distance[i][1], self.cars_distance[i][4])

                        else:
                            if self.cars_distance[i][0] in close_stopped:
                                close_stopped.remove(self.cars_distance[i][0])
                                print("Remove from list close_stopped because safe distance", 
                                    self.cars_distance[i][0],self.cars_distance[i][1], self.cars_distance[i][4])


                image = camera.read() # alway read camera for last frame ???          

                image = preprocess(image).half()
                output = self.model_trt(image).detach().cpu().numpy().flatten()
                x = float(output[0])
                self.car.steering = x * STEERING_GAIN + STEERING_BIAS
                continue
                
print("Car autonomous is loading, please wait few minutes!")
# Initial car class
car = NvidiaRacecar()

# Initial joystick controller 
try:
    joystick = JoystickController(car,controller)
except BaseException:
    pass

# Initial MQTT connection and listen on topic    
instance = Notify(car)
instance.start()

# [Nhim]: To stop: interrupt kernel first ->  run this cell

# In[ ]:


instance.stop()

# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:

instance.stop()

# In[ ]:



