# Copyright 2023 ETRI. 
# License-identifier:GNU General Public License v3.0 or later
# kwmin92@etri.re.kr, yssong00@etri.re.kr

# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program. 
# If not, see <https://www.gnu.org/licenses/>.


""" Simulation CAR1 & CAR2 & ADS class A, B, C, D, E Negotiation """

from simulation_map import *
import struct
import geo_convert
import os
import sys
import select
import datetime
from socket import *
from ursina import curve
from pyqt import *
from object import *
# 차량 움직이는 함수
car1_posi = None
car2_posi = None
bsm_msg = 0
car1_x = 0
car1_z = 0
car2_x = 0
car2_z = 0

class MainMenu(Entity):
    """ Main Menu select Class A, B, C, D, E """
    def __init__(self):
        """ init """

        super().__init__(parent = camera.ui)
        root = MyApp()

        # 시뮬레이션 초기 메뉴 세팅
        self.start_menu = Entity(parent=self, enabled=True)
        self.maps_menu = Entity(parent=self, enabled=False)
        self.main_menu = Entity(parent=self, enabled=False)
        self.position_amenu = Entity(parent=self, enabled=False)
        self.position_bmenu = Entity(parent=self, enabled=False)
        self.position_cmenu = Entity(parent=self, enabled=False)
        self.position_dmenu = Entity(parent=self, enabled=False)
        self.position_emenu = Entity(parent=self, enabled=False)
        self.garage_menu = Entity(parent=self, enabled=False)
        self.logo_row = Entity(parent=self, enabled=False)
        self.simulation = Entity(parent=self, enabled=False)

        # 프로그램 메인 메뉴 자동차
        self.menu_car = Entity(model='objects/car/solo_car.obj', texture='objects/car/white.png', collider='mesh',
                               scale=1, position=(-4.3, -3, 0), visible=True, enabled=False)
        # 프로그램 메인 메뉴 ETRI 문자
        for menu in (self.start_menu, self.main_menu):
            def animate_in_menu(menu=menu):
                for i, e in enumerate(menu.children):
                    e.original_scale = e.scale
                    e.scale -= 0.01
                    e.animate_scale(e.original_scale, delay=i * 0.05, duration=0.1, curve=curve.out_quad)

                    e.alpha = 0
                    e.animate("alpha", 0.7, delay=i * 0.05, duration=0.1, curve=curve.out_quad)
                    if hasattr(e, "text_entity"):
                        e.text_entity.alpha = 0
                        e.text_entity.animate("alpha", 1, delay=i * 0.05, duration=0.1)

        menu.on_enable = animate_in_menu
        self.menu_car.enable()
        # 프로그램 시작시 보이는 메뉴 설정
        def main_menu():
            """ main menu display """
            self.maps_menu.enable()
            self.start_menu.disable()
            self.main_menu.disable()
            self.garage_menu.disable()
            self.simulation.disable()
            self.logo_row.disable()

        def start_A(): # 우합류 시나리오 카메라 설정 및 차량 시나리오 입력
            """ start class A """
            global camera_x, camera_y, camera_z, camera_ro_x, camera_ro_y, camero_ro_z, car1_x, car1_z, car2_x, car2_z
            self.start_menu.disable()
            self.maps_menu.disable()
            self.main_menu.disable()
            self.position_amenu.enable()
            self.simulation.disable()
            self.logo_row.enable()
            camera_x = -20.208402633666992
            camera_y = -15.452710151672363
            camera_z = 13.685632705688477
            camera_ro_x = 45.571929931640625
            camera_ro_y = -178.181396484375
            camero_ro_z = 0.0
            self.case = 1
            print("우합류 시나리오가 시작됩니다.")
            back_abutton_pos = Button(text="<- B a c k", color=color.gray, scale_y=0.05, scale_x=0.2, y=0.45, x=-0.65,
                                      parent=self.position_amenu)
            simulatuon_astart_button = Button(text="S T A R T", color=color.black, scale_y=0.4, scale_x=0.7, y=0,
                                              parent=self.position_amenu)
            simulatuon_astart_button.on_click = Func(simulaion_start)
            back_abutton_pos.on_click = Func(simulation_back)

        def start_B(): # 끼어들기 시나리오 카메라 설정 및 차량 시나리오 입력
            """ start class B """
            global camera_x, camera_y, camera_z, camera_ro_x, camera_ro_y, camero_ro_z, car1_x, car1_z, car2_x, car2_z
            self.start_menu.disable()
            self.maps_menu.disable()
            self.main_menu.disable()
            self.position_bmenu.enable()
            self.simulation.disable()
            self.logo_row.enable()
            camera_x = -6.739945411682129
            camera_y = -12.982739448547363
            camera_z = 8.832342147827148
            camera_ro_x = 82.89906311035156
            camera_ro_y = 12.355425834655762
            camero_ro_z = 0.0
            self.case = 2           # 시나리오 B 상수
            print("끼어들기 시나리오가 시작됩니다.")
            self.dmm_msg = 1
            back_abutton_pos = Button(text="<- B a c k", color=color.gray, scale_y=0.05, scale_x=0.2, y=0.45, x=-0.65,
                                      parent=self.position_bmenu)
            simulatuon_astart_button = Button(text="S T A R T", color=color.black, scale_y=0.4, scale_x=0.7, y=0,
                                              parent=self.position_bmenu)
            simulatuon_astart_button.on_click = Func(simulaion_start)
            back_abutton_pos.on_click = Func(simulation_back)

        def start_C(): # 추월 시나리오 카메라 설정 및 차량 시나리오 입력
            """ start class C """
            global camera_x, camera_y, camera_z, camera_ro_x, camera_ro_y, camero_ro_z, car1_x, car1_z, car2_x, car2_z
            self.start_menu.disable()
            self.position_cmenu.enable()
            self.maps_menu.disable()
            self.main_menu.disable()
            # self.position_menu.disable()
            self.simulation.disable()
            self.logo_row.enable()
            camera_x = -6.739945411682129
            camera_y = -12.982739448547363
            camera_z = 8.832342147827148
            camera_ro_x = 82.89906311035156
            camera_ro_y = 12.355425834655762
            camero_ro_z = 0.0
            print("추월 시나리오 시작됩니다.")
            self.case = 3
            self.dmm_msg = 1
            self.dnm_msg = 1
            back_abutton_pos = Button(text="<- B a c k", color=color.gray, scale_y=0.05, scale_x=0.2, y=0.45, x=-0.65,
                                      parent=self.position_cmenu)
            simulatuon_astart_button = Button(text="S T A R T", color=color.black, scale_y=0.4, scale_x=0.7, y=0,
                                              parent=self.position_cmenu)
            simulatuon_astart_button.on_click = Func(simulaion_start)
            back_abutton_pos.on_click = Func(simulation_back)

        def start_D(): # 양보요청 1 시나리오 카메라 설정 및 차량 시나리오 입력
            "start class D"
            global camera_x, camera_y, camera_z, camera_ro_x, camera_ro_y, camero_ro_z, car1_x, car1_z, car2_x, car2_z
            self.start_menu.disable()
            self.maps_menu.disable()
            self.main_menu.disable()
            self.position_dmenu.enable()
            self.simulation.disable()
            self.logo_row.enable()
            camera_x = -20.208402633666992
            camera_y = -15.452710151672363
            camera_z = 13.685632705688477
            camera_ro_x = 45.571929931640625
            camera_ro_y = -178.181396484375
            camero_ro_z = 0.0
            self.case = 4
            back_abutton_pos = Button(text="<- B a c k", color=color.gray, scale_y=0.05, scale_x=0.2, y=0.45, x=-0.65,
                                      parent=self.position_dmenu)
            simulatuon_astart_button = Button(text="S T A R T", color=color.black, scale_y=0.4, scale_x=0.7, y=0,
                                              parent=self.position_dmenu)
            simulatuon_astart_button.on_click = Func(simulaion_start)
            back_abutton_pos.on_click = Func(simulation_back)


        def start_E(): # 양보요청 2 시나리오 카메라 설정 및 차량 시나리오 입력
            """ start class E """
            global camera_x, camera_y, camera_z, camera_ro_x, camera_ro_y, camero_ro_z, car1_x, car1_z, car2_x, car2_z
            self.start_menu.disable()

            self.maps_menu.disable()
            self.main_menu.disable()
            self.position_emenu.enable()
            self.simulation.disable()
            self.logo_row.enable()
            camera_x = 1.41703
            camera_y = -17.3364
            camera_z = -2.859
            camera_ro_x = 40.4213
            camera_ro_y = -44.0837
            camero_ro_z = 0.0
            self.case = 5
            back_abutton_pos = Button(text="<- B a c k", color=color.gray, scale_y=0.05, scale_x=0.2, y=0.45, x=-0.65,
                                      parent=self.position_emenu)
            simulatuon_astart_button = Button(text="S T A R T", color=color.black, scale_y=0.4, scale_x=0.7, y=0,
                                              parent=self.position_emenu)
            simulatuon_astart_button.on_click = Func(simulaion_start)
            back_abutton_pos.on_click = Func(simulation_back)

        def simulaion_start(): # 시작 버튼을 눌렀을 때 차량, PYQT, 맵 보이도록 설정
            """ start simulation CAR1 & CAR2 """
            global camera_x, camera_y, camera_z, camera_ro_x, camera_ro_y, camero_ro_z
            self.maps_menu.disable()
            self.main_menu.disable()
            self.position_amenu.disable()
            self.position_bmenu.disable()
            self.position_cmenu.disable()
            self.position_dmenu.disable()
            self.position_emenu.disable()
            self.simulation.enable()
            self.logo_row.disable()
            if self.case == 1 or self.case == 2:
                self.car1 = Car1(case = self.case, speed= self.car1_speed)
                self.car2 = Car2(case=self.case, speed= self.car2_speed)
            elif self.case == 3:
                self.car2 = Car2(case=self.case, speed= self.car2_speed)
            else:
                self.e_car = E_car(case = self.case, speed= self.car2_speed)
                self.e_car_speed = self.car2_speed
                self.car1_speed = 0
            self.ads_car = ADS_car(case = self.case)
            self.recv = ADS()
            map()
            root.show()
            camera.x, camera.y, camera.z = camera_x, camera_y, camera_z
            camera.rotation_x, camera.rotation_y, camera.rotation_z = camera_ro_x, camera_ro_y, camero_ro_z
            self.car_create = 1

        def simulation_back(): # 시뮬레이션 back 버튼 눌렀을 때 초기 화면 및 차량 오브젝트 삭제
            """ display back """
            self.start_menu.enable()
            self.main_menu.disable()
            self.position_amenu.disable()
            self.position_bmenu.disable()
            self.position_cmenu.disable()
            self.position_dmenu.disable()   
            self.position_emenu.disable()
            self.simulation.disable()
            self.logo_row.disable()
            self.remain_distance = self.ri = self.dnm_msg = self.dmm_msg = self.speed_ch = self.pim_msg = 0
            # 카메라 위치 초기화
            camera.x, camera.y, camera.z = 0.0, 0.0, - 20.0
            camera.rotation_x, camera.rotation_y, camera.rotation_z = -0.0, - 0.0, 0.0
            # update 변수 초기화 및 속도 조절 패널 비활성화 및 속도 초기화 및 차량 오브젝트 삭제
            self.wp.disable()
            self.wp2.disable()
            self.car1_speed = 20 # 차량들 속도도 초기화
            self.car2_speed = 15
            self.e_car_speed = 15
            if self.car_create == 1:
                if self.case == 1 or self.case == 2:
                    self.car1.disable()
                    self.car2.disable()
                elif self.case == 3:
                    self.car2.disable()
                else:
                    self.e_car.disable()
                self.car_create = 0
                self.recv.disable()
                self.ads_car.disable()

        # Etri 로고 추가할 것
        self.e_title = Entity(model='objects/logo/E.obj', color=color.blue, scale=15, position=(-0.24, 0.25, 0)
                              , rotation=(100, 20, 180), parent=self.start_menu)
        self.t_title = Entity(model='objects/logo/T.obj', color=color.blue, scale=15, position=(-0.24, 0.25, 0)
                              ,rotation=(100, 20, 180), parent=self.start_menu)
        self.r_title = Entity(model='objects/logo/R.obj', color=color.red, scale=15, position=(-0.24, 0.25, 0)
                              , rotation=(100, 20, 180), parent=self.start_menu)
        self.i_title = Entity(model='objects/logo/I.obj', color=color.blue, scale=15, position=(-0.24, 0.25, 0)
                              , rotation=(100, 20, 180), parent=self.start_menu)

        case1_track_button = Button(text="C A S E A", color=color.black, scale_y=0.1, scale_x=0.3, y=0.05
                                    , x=-0.5, parent=self.start_menu)
        case2_track_button = Button(text="C A S E B", color=color.black, scale_y=0.1, scale_x=0.3, y=0.05
                                    , x=0, parent=self.start_menu)
        case3_track_button = Button(text="C A S E C", color=color.black, scale_y=0.1, scale_x=0.3, y=0.05
                                    , x=0.5, parent=self.start_menu)
        case4_track_button = Button(text="C A S E D", color=color.black, scale_y=0.1, scale_x=0.3, y=-0.15
                                    , x=-0.25, parent=self.start_menu)
        case5_track_button = Button(text="C A S E E", color=color.black, scale_y=0.1, scale_x=0.3, y=-0.15
                                    , x=0.25, parent=self.start_menu)

        case1_track_button.on_click = Func(start_A)
        case2_track_button.on_click = Func(start_B)
        case3_track_button.on_click = Func(start_C)
        case4_track_button.on_click = Func(start_D)
        case5_track_button.on_click = Func(start_E)

        # case1

        self.abcd_title_r = Entity(model='objects/logo/abcd.obj', color=color.black, scale=0.11
                                   ,position=(0.585, -0.35, 0.09), rotation=(180, 90, 160), parent=self.logo_row)
        self.eti_title_r = Entity(model='objects/logo/ETI.obj', color=color.blue, scale=8
                                  , position=(0.585, -0.33, 0), rotation=(90, 0, 90), parent=self.logo_row)
        self.r_title_r = Entity(model='objects/logo/R_MID.obj', color=color.red, scale=8
                                , position=(0.585, -0.33, 0), rotation=(90, 0, 90), parent=self.logo_row)

        def quit_app():
            application.quit()
            if self.car.multiplayer_update:
                os._exit(0)

        back_button_sim = Button(text="<- B a c k", color=color.gray, scale_y=0.05, scale_x=0.2
                                 , y=0.45, x=-0.65,parent=self.simulation)
        back_button_sim.on_click = Func(simulation_back)

# 차량 기본 정보 설정
        self.count = 1
        self.car1_speed = 20
        self.car2_speed = 15
        self.e_car_speed = 15
        self.car_create = 0
        self.case = 0
        self.ads_speed = 0

        # 차량용 UI 단말 소켓 - Object.py 에서 소켓연결 설정, 330-331 line delete
        # self.ui_client = socket(AF_INET, SOCK_DGRAM)
        # self.ui_port = ("192.168.1.203", 63011)

        # PYQT 통신 로그 통신
        self.qt_log_server = socket(AF_INET, SOCK_DGRAM)
        self.qt_iport = ('localhost', 55555)

        # 속도 변환 윈도우
        self.speed1_text = InputField(default_value=str(self.car1_speed), limit_content_to="0123456789.")
        self.speed1_button = Button(text='Submit', color=color.azure)
        self.speed2_text = InputField(default_value=str(self.car2_speed), limit_content_to="0123456789.")
        self.wp = WindowPanel(
            position = (-0.6375, 0.419444, -0.000914464),
            title = 'car_speed_panel',
            content=(self.speed1_text, self.speed2_text, self.speed1_button),
            popup = False,
            enabled = False
        )
        self.speed3_text = InputField(default_value=str(self.car2_speed), limit_content_to="0123456789.")
        self.speed2_button = Button(text='Submit', color=color.azure)
        self.wp2 = WindowPanel(
            position = (-0.6375, 0.419444, -0.000914464),
            title = 'car_speed_panel',
            content=(self.speed3_text, self.speed2_button),
            popup = False,
            enabled = False
        )

    def update(self): # 자동 업데이트 반복
        """ display update """

        self.menu_car.enable()
        self.image_car_moving()
        self.send_speed()
        if self.car_create == 1:
            if self.case == 1 or self.case == 2:
                self.wp.enable()
            else:
                self.wp2.enable()
            self.speed1_button.on_click = self.ch1_car_speed
            self.speed2_button.on_click = self.ch2_car_speed
            self.ads_speed = self.ads_car.speed
    def ch1_car_speed(self):
        """ car1_speed """
        self.car1.speed = int(self.speed1_text.text)
        self.car1_speed = int(self.speed1_text.text)
        self.car2.speed = int(self.speed2_text.text)
        self.car2_speed = int(self.speed2_text.text)
    def ch2_car_speed(self):
        """ e-car speed """
        if self.case == 3:
            self.car2.speed = int(self.speed3_text.text)
            self.car2_speed = int(self.speed2_text.text)
        else:
            self.e_car.speed = int(self.speed3_text.text)
            self.e_car_speed = self.e_car.speed
            self.car2_speed = int(self.speed2_text.text)
    def send_speed(self):
        """ send speed """
        if self.case == 4 or self.case == 5:
            if self.ads_speed == 0:
                ads_speed = "000"
            elif self.ads_speed < 100:
                ads_speed = "0"+str(int(self.ads_speed))
            else:
                ads_speed = str(int(self.ads_speed))
            if self.car1_speed == 0:
                car1_speed = "000"
            elif self.car1_speed < 100:
                car1_speed = "0"+str(self.car1_speed)
            else:
                car1_speed = str(self.car1_speed)
            if self.e_car_speed == 0:
                car2_speed = "000"
            elif self.e_car_speed < 100:
                car2_speed = "0"+str(self.e_car_speed)
            else:
                car2_speed = str(self.e_car_speed)
        else:
            if self.ads_speed == 0:
                ads_speed = "000"
            elif self.ads_speed < 100:
                ads_speed = "0"+str(int(self.ads_speed))
            else:
                ads_speed = str(int(self.ads_speed))
            if self.car1_speed == 0:
                car1_speed = "000"
            elif self.car1_speed < 100:
                car1_speed = "0"+str(self.car1_speed)
            else:
                car1_speed = str(self.car1_speed)
            if self.car2_speed == 0:
                car2_speed = "000"
            elif self.car2_speed < 100:
                car2_speed = "0"+str(self.car2_speed)
            else:
                car2_speed = str(self.car2_speed)

        speed = "speed" + ads_speed + car1_speed + car2_speed

        self.qt_log_server.sendto(speed.encode(), self.qt_iport)

    def image_car_moving(self):
        """ display image car """
        self.eti_title_r.rotation += (0, 0.3 * 2, 0)
        self.r_title_r.rotation += (0, 0.3 * 2, 0)
        if self.start_menu.enabled:
            camera.rotation = (0, 2, 0)
        self.menu_car.rotation += (0, 0.09 * 2, 0)
        if self.count == 1:
            self.e_title.position += (0, 0.0002 * 2, 0)
            self.t_title.position += (0, 0.00025 * 2, 0)
            self.r_title.position += (0, 0.00028 * 2, 0)
            self.i_title.position += (0, 0.00022 * 2, 0)
        elif self.count == 2:
            self.e_title.position += (0, -0.0002 * 2, 0)
            self.t_title.position += (0, -0.00025 * 2, 0)
            self.r_title.position += (0, -0.00028 * 2, 0)
            self.i_title.position += (0, -0.00022 * 2, 0)

        if self.e_title.position[1] >= 0.2:
            self.count = 2
        elif self.e_title.position[1] <= 0.15:
            self.count = 1
