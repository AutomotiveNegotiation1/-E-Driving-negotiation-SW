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


""" socket connection simul CAR & ADS """

import datetime as dt
from socket import *
from ursina import *
import struct
import select
import geo_convert as geo
from haversine import *

ads_tmp_id = None
rotation = 0
position = 0
dmm_recv = 0
msg = 0

""" socket connection simul CAR & ADS IP Setting """

ads_ip ="localhost"  #192.168.1.100, 자율주행 차량 SW IP, 동일 IP 구성 필요
ui_ip = "localhost" #192.168.1.203
my_ip = "localhost"  #192.168.1.202 #31252 server port

class ADS(Entity):
    """ ADS connection and Send/Receive Data """
    def __init__(self):
        """ init """
        super().__init__()

    def update(self):
        """ update ADS data """
        global msg
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((my_ip, 31252))
        ready = select.select([self.socket], [], [], 0.02)
        if ready[0]:
            msg, addr = self.socket.recvfrom(1024)
            print("receive")

        self.socket.close()

class ADS_car(Entity):
    """ ADS CAR image """
    def __init__(self, case):
        """ init """
        super().__init__(model='objects/car/solo_car.obj',
            collider='mesh',
            texture='objects/car/white.png',
            scale=0.04)
        self.case = case
        self.qt_log_server = socket(AF_INET, SOCK_DGRAM)
        self.qt_iport = ('localhost', 55555)
        self.dnm_msg = 0
        self.__speed = 0
        self.speed_ch = 0

    def update(self):
        """ ADS update data/state """
        global dmm_recv, msg, ads_tmp_id
        self.msg = msg
        if type(self.msg).__name__ == "bytes":
            msg_id = struct.unpack('>b', self.msg[:1])
            # BSM 메시지
            if msg_id[0] == 1:
                self.ads_bsm = struct.unpack('<B H H B I H i i H i h h b', self.msg[0:31])
                if self.ads_bsm[10] >= 8192:
                    de1_Trans_Speed = bin(self.ads_bsm[10] >> 13)
                    int_de1_Trans = int(de1_Trans_Speed)
                    de2_Trans_Speed = bin(int_de1_Trans << 13)
                    self.__speed = (self.ads_bsm[10] - int(de2_Trans_Speed, 2)) * 0.02
                else:
                    self.__speed = self.ads_bsm[10] * 0.02 * 3.6
                self.position = (
                    (geo.wgs842tm(self.ads_bsm[6], self.ads_bsm[7])[0] - 232804.0) / 50, -18.95,
                    (((geo.wgs842tm(self.ads_bsm[6], self.ads_bsm[7])[1]) - 420248) / 50) - 1.02 - 0.69)
                self.rotation_y = self.ads_bsm[11] * 0.0125
                msg = "[ADS >> SIMULATOR] MSG_TYPE : BSM, LAT : " + str(self.ads_bsm[6]) + ", LONG : " + str(
                    self.ads_bsm[7]) + ", HEADING : " + str(self.rotation_y) + ", SPEED : " + str(self.__speed)
                self.qt_log_server.sendto(msg.encode(), self.qt_iport)
            # DMM
            if msg_id[0] == 3:
                dmm_msg = struct.unpack('<B H H I H B', self.msg)
                # DMM 메시지의 파싱이 시작되었다는 표시
                print("DMM is arrived")
                # ADS가 payload에 추가한 ads Tmp_id
                self.ads_id = dmm_msg[3]                
                # 좌차로 변경 or 우차로 변경 메시지가 수신되면 car2의 차량이 속도를 늦춥니다.
                if dmm_msg[4] == 1:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id) 
                    msg += ", 차로 내 직진이 수신되었습니다. "
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                elif dmm_msg[4] == 2:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id) 
                    msg += ", 좌차로 변경이 수신되었습니다. "
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                elif dmm_msg[4] == 3:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id) 
                    msg += ", 우차로 변경이 수신되었습니다."
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                elif dmm_msg[4] == 4:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id) 
                    msg += ", 직진이 수신되었습니다. "
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                elif dmm_msg[4] == 5:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id) 
                    msg += ", 좌회전이 수신되었습니다. "
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                elif dmm_msg[4] == 6:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id)
                    msg += ", 우회전이 수신되었습니다."
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                elif dmm_msg[4] == 7:
                    msg = "[ADS >> SIMULATOR] MSG_TYPE : DMM, 끼어드는 차량 ID = " + str(self.ads_id) 
                    msg += ", 유턴이 수신되었습니다."
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)

                if dmm_msg[4] == 2 or msg[3] == 3:
                    if self.case == 2 and self.speed_ch == 0:  # 속도가 바뀌지 않았을때만 작동하도록
                        # 차량 속도 변환 -10km/h
                        print("차량의 속도가 변경됩니다.")
                        dmm_recv = 1
                        self.speed_ch = 1
            # DNM Req메시지
            if msg_id[0] == 4:
                self.dnm_msg = struct.unpack('<B H H I I B', self.msg)
                ads_tmp_id = struct.pack('>B I', 1, self.dnm_msg[3])
                msg = "[ADS -> Car2] MSG_TYPE : DNM Req"
                self.qt_log_server.sendto(msg.encode(), self.qt_iport)
            # DNM Done메시지
            if msg_id[0] == 6:
                try:
                    msg = "[ADS -> Car2] MSG_TYPE : DNM Ack, 협력주행 끝"
                    self.qt_log_server.sendto(msg.encode(), self.qt_iport)
                    ads_tmp_id = struct.pack('>B I', 0, self.dnm_msg[3])
                except BaseException:
                    pass
    @property
    def speed(self):
        """ speed """
        return self.__speed

    @speed.setter
    def speed(self, s):
        """ set speed """
        self.__speed = s

class Car1(Entity):
    """ Simul CAR1 """

    def __init__(self, case, speed):
        """ init """
        super().__init__(
            model='objects/car/solo_car.obj',
            collider='mesh',
            texture='objects/car/green.png',
            scale=0.04)
        self.case = case
        self.__speed = speed
        self.temp_id = 1
        self.car1_tick1 = dt.datetime.now().strftime('%S%f')[:-3]
        self.result = []
        # 경로 선택
        if self.case == 1:
            self.case_a()
            self.car1_ri = 70
        elif self.case == 2:
            self.case_b()
            self.car1_ri = 50
        # 기본 변수
        self.msg_cnt = 0
        self.timer = 0
        self.car1_rd = 0
        self.ch_while = 0
        self.trans = 2 << 13
        self.car1_reset_position = [self.result[self.car1_ri][0], self.result[self.car1_ri][1]]
        self.new_p2p_distance = 0
        # 통신 부분
        # Car1 -> ADS
        self.client = socket(AF_INET, SOCK_DGRAM)
        self.client_addr = (ads_ip, 63113)
        # Car1 -> PYQT
        self.qt_log_server = socket(AF_INET, SOCK_DGRAM)
        self.qt_iport = ('localhost', 55555)
        # Car1 -> UI
        self.ui_client = socket(AF_INET, SOCK_DGRAM)
        self.ui_port = (ui_ip, 63011)

        self.before_speed = 0
        self.state = 1

    def update(self):
        """ update """
        self.key_control()
        self.car1_tick2 = self.car1_tick1
        self.car1_tick1 = dt.datetime.now().strftime('%S%f')[:-3]
        self.car1_tick = (float(self.car1_tick1) - float(self.car1_tick2))
        if self.car1_tick < 0:
            self.car1_tick += 60000
        self.timer += self.car1_tick
        # 시작점
        start_dot = [self.result[self.car1_ri][0], self.result[self.car1_ri][1]]
        # 다음점
        next_dot = [self.result[self.car1_ri + 1][0], self.result[self.car1_ri + 1][1]]
        # 점 사이의 거리
        d2d_distance = haversine(start_dot, next_dot, unit=Unit.METERS)
        # 차량의 이동 거리
        if self.state == 0:
            car1_md = 0
        else:
            car1_md = float(self.__speed / 3600 * self.car1_tick)
        # 남은 거리
        car1_rd = car1_md - d2d_distance + self.car1_rd
        line_check = self.car1_ri
        while car1_rd > 0:
            self.car1_ri += 1
            # out of range 방지
            if self.case == 1 and self.car1_ri == len(self.result) - 1:
                self.car1_ri = 70
                self.car1_rd = 0
            elif self.case == 2 and self.car1_ri == len(self.result) - 1:
                self.car1_ri = 50
                self.car1_rd = 0
            else:
                start_dot = [self.result[self.car1_ri][0], self.result[self.car1_ri][1]]
                next_dot = [self.result[self.car1_ri + 1][0], self.result[self.car1_ri + 1][1]]
                self.new_p2p_distance = haversine(start_dot, next_dot, unit=Unit.METERS)
                car1_md = car1_rd
                car1_rd -= self.new_p2p_distance
                self.ch_while = 1
        if car1_rd <= 0:
            dx = next_dot[0] - start_dot[0]
            dy = next_dot[1] - start_dot[1]
            if self.ch_while == 0:
                car1_x = (car1_md + self.car1_rd) * dx / d2d_distance
                car1_y = (car1_md + self.car1_rd) * dy / d2d_distance
            elif self.ch_while == 1:
                car1_x = car1_md * dx / self.new_p2p_distance
                car1_y = car1_md * dy / self.new_p2p_distance
            wgs_x = start_dot[0] + car1_x
            wgs_y = start_dot[1] + car1_y
            x = float((geo.wgs842tm(wgs_x, wgs_y)[0] - 232804.0) / 50)
            y = -18.95
            z = float((((geo.wgs842tm(wgs_x, wgs_y)[1]) - 420248) / 50) - 1.02 - 0.69)
            self.position = (x, y, z)
            if line_check == self.car1_ri:
                self.car1_rd += car1_md
            else:
                self.car1_rd = car1_md
            self.rotation_y = self.result[self.car1_ri][2]

        elif car1_rd == 0:
            start_dot = [self.result[self.car1_ri][0], self.result[self.car1_ri][1]]
            self.position = (geo.wgs842tm(start_dot[0], start_dot[1])[0] - 232804.0) / 50, -18.95, (
                    (((geo.wgs842tm(start_dot[0], start_dot[1])[1]) - 420248) / 50) - 1.02 - 0.69)
            self.rotation_y = self.result[self.car1_ri][2]
        if self.timer >= 100:
            self.timer = 0
            [x, y, z] = self.position
            self.bsm_id = (1).to_bytes(1, byteorder="big", signed=True)
            self.bsm_CRC_16 = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Packet = (43).to_bytes(2, byteorder="big", signed=True)
            self.bsm_msgcnt = (self.msg_cnt).to_bytes(1, byteorder="big", signed=True)
            self.bsm_tmpid = (self.temp_id).to_bytes(4, byteorder="big", signed=True)
            self.bsm_DSecond = (0).to_bytes(2, byteorder="big", signed=True)
            # LAT, LONG 변환
            self.x1 = (x * 50) + 232804
            self.z1 = (z + 1.02 + 0.69) * 50 + 420248
            self.lat_car1 = int(round(geo.tm2wgs84(self.x1, self.z1)[0], 7) * 10000000)
            self.long_car1 = int(round(geo.tm2wgs84(self.x1, self.z1)[1], 7) * 10000000)
            self.bsm_lat1 = self.lat_car1.to_bytes(4, byteorder="big", signed=True)
            self.bsm_long1 = self.long_car1.to_bytes(4, byteorder="big", signed=True)
            self.bsm_ELev = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_PosAccy = (0).to_bytes(4, byteorder="big", signed=True)
            self.msg_speed_car1 = self.__speed / 3.6 / 0.02
            self.trans_speed_car1 = self.trans + int(self.msg_speed_car1)
            self.bsm_Trans_Speed1 = (self.trans_speed_car1).to_bytes(2, byteorder="big", signed=True)
            self.msg_heading_car1 = int(self.rotation_y / 0.0125)
            self.bsm_Heading1 = (self.msg_heading_car1).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Angle = (0).to_bytes(1, byteorder="big", signed=True)
            self.bsm_Acc = (0).to_bytes(7, byteorder="big", signed=True)
            self.bsm_Brake = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Size = (0).to_bytes(3, byteorder="big", signed=True)
            self.bsm = (
                    self.bsm_id + self.bsm_CRC_16 + self.bsm_Packet + self.bsm_msgcnt + self.bsm_tmpid 
                    + self.bsm_DSecond + self.bsm_lat1 + self.bsm_long1 + self.bsm_ELev + self.bsm_PosAccy 
                    + self.bsm_Trans_Speed1 + self.bsm_Heading1 + self.bsm_Angle + self.bsm_Acc 
                    + self.bsm_Brake + self.bsm_Size)
            self.msg_cnt += 1
            if self.msg_cnt == 128:
                self.msg_cnt = 0
            self.client.sendto(self.bsm, self.client_addr)
            self.ui_client.sendto(self.bsm, self.ui_port)
            msg = "[CAR1 >> ADS] MSG_TYPE : BSM, LAT : " + str(self.lat_car1) + ", LONG : " + str(
                self.long_car1) + ", HEADING : " + str(self.rotation_y) + ", SPEED : " + str(self.__speed)
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)
        self.ch_while = 0

    @property
    def speed(self):
        """ speed """
        return self.__speed

    @speed.setter
    def speed(self, s):
        """ set speed """
        self.__speed = s

    def key_control(self):
        """ keyboard control """
        if held_keys["r"]:  # 포지션 리셋
            print("초기 위치로 설정됩니다.")
            if self.case == 1:
                self.car1_ri = 70
                self.car1_rd = 0
            elif self.case == 2:
                self.car1_ri = 50
                self.car1_rd = 0
        elif held_keys["d"]:
            print("다시 주행을 시작합니다.")
            self.state = 1
        elif held_keys["s"]:
            print("차량의 움직임을 멈춥니다.")
            self.state = 0

    def case_a(self):
        """ case a simulation car1 location """
        with open("convert_a.txt", "r") as fp:
            j = 0
            ri = 0
            for i in fp.readlines():
                tmp = i.split(",")
                tmp[2] = tmp[2].replace("\n", "")

                if j == 0:
                    self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), 0.0])
                    ri += 1
                    j += 1

                else:
                    if 1 <= ri:
                        first = (float(self.result[ri - 1][0]), float(self.result[ri - 1][1]))
                        second = (float(tmp[0]) / 10000000, float(tmp[1]) / 10000000)
                        c = haversine(first, second, unit=Unit.METERS)
                        self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), c])
                        ri += 1

    def case_b(self):
        """ case b simulation car1 map """
        with open("convert_bc.txt", "r") as fp:
            j = 0
            ri = 0
            for i in fp.readlines():
                tmp = i.split(",")
                tmp[2] = tmp[2].replace("\n", "")

                if j == 0:
                    self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), 0.0])
                    ri += 1
                    j += 1

                else:
                    if 1 <= ri:
                        first = (float(self.result[ri - 1][0]), float(self.result[ri - 1][1]))
                        second = (float(tmp[0]) / 10000000, float(tmp[1]) / 10000000)
                        c = haversine(first, second, unit=Unit.METERS)
                        self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), c])
                        ri += 1


class Car2(Entity):
    """ Simul CAR2 """
    def __init__(self, case, speed):
        """ init """
        super().__init__(
            model='objects/car/solo_car.obj',
            collider='mesh',
            texture='objects/car/yellow.png',
            scale=0.04)
        self.case = case
        self.__speed = speed
        self.temp_id = 2
        self.car2_tick1 = dt.datetime.now().strftime('%S%f')[:-3]
        self.result = []
        if self.case == 1:
            self.case_a()
        elif self.case == 2 or self.case == 3:
            self.case_bc()
        # 기본 변수
        self.dnm_done_check = 0
        self.car2_ri = 0
        self.car2_rd = 0
        self.ch_while = 0
        self.car2_reset_position = [self.result[self.car2_ri][0], self.result[self.car2_ri][1]]
        self.timer = 0
        self.msg_cnt = 0
        self.trans = 2 << 13
        self.new_p2p_distance = 0
        # 통신 부분
        # PYQT
        self.qt_log_server = socket(AF_INET, SOCK_DGRAM)
        self.qt_iport = ('localhost', 55555)
        # Car2 -> ADS
        self.client = socket(AF_INET, SOCK_DGRAM)
        self.client_addr = (ads_ip, 63113)
        # Car2 -> UI
        self.ui_client = socket(AF_INET, SOCK_DGRAM)
        self.ui_port = (ui_ip, 63011)

        self.state = 1
        self.before_speed = 0

    def update(self):
        """ update """
        global ads_tmp_id, dmm_recv
        if dmm_recv == 1:
            self.car2_fir_sp = self.__speed
            self.__speed -= 10
            print(self.car2_fir_sp, " >>>> ", self.__speed)
            msg = "[CAR1,2 >> ADS] MSG_TYPE : DMM, 차량의 속도 변경\nCAR2 : " + str(
                self.car2_fir_sp) + ">>> " + str(self.__speed)
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)
            dmm_recv = 0

        self.key_control()
        self.car2_tick2 = self.car2_tick1
        self.car2_tick1 = dt.datetime.now().strftime('%S%f')[:-3]
        self.car2_tick = (float(self.car2_tick1) - float(self.car2_tick2))
        if self.car2_tick < 0:
            self.car2_tick += 60000
        self.timer += self.car2_tick
        # 시작점
        start_dot = [self.result[self.car2_ri][0], self.result[self.car2_ri][1]]
        # 다음점
        next_dot = [self.result[self.car2_ri + 1][0], self.result[self.car2_ri + 1][1]]

        # 점 사이의 거리
        d2d_distance = haversine(start_dot, next_dot, unit=Unit.KILOMETERS)
        # 차량의 이동 거리
        if self.state == 0:
            car2_md = 0
        else:
            car2_md = float(self.__speed / 3600 / 1000 * self.car2_tick)  # 킬로 미터 변환 및 밀리초 계산
        # 남은 거리
        car2_rd = car2_md - d2d_distance + self.car2_rd
        line_check = self.car2_ri
        while car2_rd > 0 and car2_md:
            self.car2_ri += 1
            # out of range 방지
            if self.case == 1 and self.car2_ri == len(self.result) - 71:
                self.car2_ri = 0
                self.car2_rd = 0
            elif self.case == 2 and self.car2_ri == len(self.result) - 51:
                self.car2_ri = 0
                self.car2_rd = 0
            elif self.case == 3 and self.car2_ri == len(self.result) - 1:
                self.car2_ri = 0
                self.car2_rd = 0
            else:
                start_dot = [self.result[self.car2_ri][0], self.result[self.car2_ri][1]]
                next_dot = [self.result[self.car2_ri + 1][0], self.result[self.car2_ri + 1][1]]
                self.new_p2p_distance = haversine(start_dot, next_dot, unit=Unit.METERS)
                car2_md = car2_rd
                car2_rd -= self.new_p2p_distance
                self.ch_while = 1
        if car2_rd < 0:
            dx = next_dot[0] - start_dot[0]
            dy = next_dot[1] - start_dot[1]
            if self.ch_while == 0:
                car2_x = (car2_md + self.car2_rd) * dx / d2d_distance
                car2_y = (car2_md + self.car2_rd) * dy / d2d_distance
            elif self.ch_while == 1:
                car2_x = car2_md * dx / self.new_p2p_distance
                car2_y = car2_md * dy / self.new_p2p_distance
            wgs_x = start_dot[0] + car2_x
            wgs_y = start_dot[1] + car2_y
            x = float((geo.wgs842tm(wgs_x, wgs_y)[0] - 232804.0) / 50)
            y = -18.95
            z = float((((geo.wgs842tm(wgs_x, wgs_y)[1]) - 420248) / 50) - 1.02 - 0.69)
            self.position = (x, y, z)
            if line_check == self.car2_ri:
                self.car2_rd += car2_md
            else:
                self.car2_rd = car2_md
            self.rotation_y = self.result[self.car2_ri][2]
        elif car2_rd == 0:
            start_dot = [self.result[self.car2_ri][0], self.result[self.car2_ri][1]]
            self.position = (geo.wgs842tm(start_dot[0], start_dot[1])[0] - 232804.0) / 50, -18.95, (
                    (((geo.wgs842tm(start_dot[0], start_dot[1])[1]) - 420248) / 50) - 1.02 - 0.69)
            self.rotation_y = self.result[self.car2_ri][2]
        if self.timer >= 100:
            self.timer = 0
            # BSM 메시지 보내기
            [x, y, z] = self.position
            self.bsm_id = (1).to_bytes(1, byteorder="big", signed=True)
            self.bsm_CRC_16 = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Packet = (43).to_bytes(2, byteorder="big", signed=True)
            self.bsm_msgcnt = (self.msg_cnt).to_bytes(1, byteorder="big", signed=True)
            self.bsm_tmpid2 = (self.temp_id).to_bytes(4, byteorder="big", signed=True)
            self.bsm_DSecond = (0).to_bytes(2, byteorder="big", signed=True)
            # LAT, LONG 변환
            self.x2 = (x * 50) + 232804
            self.z2 = (z + 1.02 + 0.69) * 50 + 420248
            self.lat_car2 = int(round(geo.tm2wgs84(self.x2, self.z2)[0], 7) * 10000000)
            self.long_car2 = int(round(geo.tm2wgs84(self.x2, self.z2)[1], 7) * 10000000)
            self.bsm_lat2 = self.lat_car2.to_bytes(4, byteorder="big", signed=True)
            self.bsm_long2 = self.long_car2.to_bytes(4, byteorder="big", signed=True)
            self.bsm_ELev = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_PosAccy = (0).to_bytes(4, byteorder="big", signed=True)
            # # 속도변환
            # if self.state == 0:
            #     self.__speed = self.before_speed
            self.msg_speed_car2 = self.__speed / 3.6 / 0.02
            self.trans_speed_car2 = self.trans + int(self.msg_speed_car2)
            self.bsm_Trans_Speed2 = (self.trans_speed_car2).to_bytes(2, byteorder="big", signed=True)
            self.msg_heading_car2 = int(self.rotation_y / 0.0125)
            self.bsm_Heading2 = (self.msg_heading_car2).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Angle = (0).to_bytes(1, byteorder="big", signed=True)
            self.bsm_Acc = (0).to_bytes(7, byteorder="big", signed=True)
            self.bsm_Brake = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Size = (0).to_bytes(3, byteorder="big", signed=True)
            self.bsm = (
                    self.bsm_id + self.bsm_CRC_16 + self.bsm_Packet + self.bsm_msgcnt + self.bsm_tmpid2 
                    + self.bsm_DSecond + self.bsm_lat2 + self.bsm_long2 + self.bsm_ELev + self.bsm_PosAccy 
                    + self.bsm_Trans_Speed2 + self.bsm_Heading2 + self.bsm_Angle + self.bsm_Acc + self.bsm_Brake 
                    + self.bsm_Size)
            self.msg_cnt += 1
            if self.msg_cnt == 128:
                self.msg_cnt = 0
            self.client.sendto(self.bsm, self.client_addr)
            self.ui_client.sendto(self.bsm, self.ui_port)
            # pyqt로 로그 메시지 보내기
            msg = "[CAR2 >> ADS] MSG_TYPE : BSM, LAT : " + str(self.lat_car2) + ", LONG : " + str(
                self.long_car2) + ", HEADING : " + str(self.rotation_y) + ", SPEED : " + str(self.__speed)
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)

        if type(ads_tmp_id).__name__ == "bytes":
            self.DNM()

        self.ch_while = 0

    @property
    def speed(self):
        """ speed """
        return self.__speed

    @speed.setter
    def speed(self, s):
        """ setting speed """
        self.__speed = s
    def DNM(self):
        """ make msg """
        DNM_msg = struct.unpack('>B I', ads_tmp_id)
        if DNM_msg[0] == 1:
            self.DNM_ID = (5).to_bytes(1, byteorder="big", signed=True)
            self.DNM_CRC = (0).to_bytes(2, byteorder="big", signed=True)
            self.DNM_PL = (14).to_bytes(2, byteorder="big", signed=True)
            self.Sender = (2).to_bytes(4, byteorder="big", signed=True)
            self.Receiver = (DNM_msg[1]).to_bytes(4, byteorder="big", signed=True)
            # self.Receiver = (5678).to_bytes(4, byteorder="big", signed=True)
            self.Agreement = (1).to_bytes(1, byteorder="big", signed=True)
            self.DNM_Rep = (self.DNM_ID + self.DNM_CRC + self.DNM_PL + self.Sender + self.Receiver + self.Agreement)
            self.client.sendto(self.DNM_Rep, self.client_addr)
            msg = "[CAR2 >> ADS] MSG_TYPE : DNM Rep, 협력 주행 동의하였습니다. "
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)
        elif DNM_msg[0] == 0 and self.dnm_done_check < 5:
            msg = "협력 주행이 마무리되어 DNM_reponse를 보내지 않습니다."
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)
            self.dnm_done_check += 1
    def key_control(self):
        """ keyboard control """
        if held_keys["r"]:  # 포지션 리셋
            print("초기 위치로 설정됩니다.")
            self.car2_ri = 0
            self.car2_rd = 0
            self.dnm_done_check = 0
        elif held_keys["d"]:
            print("다시 주행을 시작합니다.")
            self.state = 1
        elif held_keys["s"]:
            print("차량의 움직임을 멈춥니다.")
            self.state = 0

    def case_a(self):
        """ case a simulation car2 map """
        with open("convert_a.txt", "r") as fp:
            j = 0
            ri = 0
            for i in fp.readlines():
                tmp = i.split(",")
                tmp[2] = tmp[2].replace("\n", "")

                if j == 0:
                    self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), 0.0])
                    ri += 1
                    j += 1

                else:
                    if 1 <= ri:
                        first = (float(self.result[ri - 1][0]), float(self.result[ri - 1][1]))
                        second = (float(tmp[0]) / 10000000, float(tmp[1]) / 10000000)
                        c = haversine(first, second, unit=Unit.METERS)
                        self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), c])
                        ri += 1

    def case_bc(self):
        """ case bc simulation car2 map """
        with open("convert_bc.txt", "r") as fp:
            j = 0
            ri = 0
            for i in fp.readlines():
                tmp = i.split(",")
                tmp[2] = tmp[2].replace("\n", "")

                if j == 0:
                    self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), 0.0])
                    ri += 1
                    j += 1

                else:
                    if 1 <= ri:
                        first = (float(self.result[ri - 1][0]), float(self.result[ri - 1][1]))
                        second = (float(tmp[0]) / 10000000, float(tmp[1]) / 10000000)
                        c = haversine(first, second, unit=Unit.METERS)
                        self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), c])
                        ri += 1


class E_car(Entity):
    """ Simul CAR3 - Emergency car """
    def __init__(self, case, speed):
        """ init """
        super().__init__(
            model='objects/car/ambulance.obj',
            collider='mesh',
            texture='objects/car/ambulance.tga',
            scale=0.01)
        self.case = case
        self.__speed = speed
        self.temp_id = 2
        self.tick1 = dt.datetime.now().strftime('%S%f')[:-3]
        self.result = []
        if self.case == 4:
            self.case_d()
        elif self.case == 5:
            self.case_e()
        # 기본 변수
        self.new_d2d_distance = 0
        self.ri = 0
        self.rd = 0
        self.ch_while = 0
        self.reset_position = [self.result[self.ri][0], self.result[self.ri][1]]
        self.t3 = 0
        self.msg_cnt = 0
        self.trans = 2 << 13
        # 통신 부분
        # PYQT
        self.qt_log_server = socket(AF_INET, SOCK_DGRAM)
        self.qt_iport = ('localhost', 55555)
        # Car2 -> ADS
        self.client = socket(AF_INET, SOCK_DGRAM)
        self.client_addr = (ads_ip, 63113)
        # Car2 -> UI
        self.ui_client = socket(AF_INET, SOCK_DGRAM)
        self.ui_port = (ui_ip, 63011)

        self.state = 1
        self.maneuver_type = 2

    def update(self):
        """ update """
        self.key_control()
        self.tick2 = self.tick1
        self.tick1 = dt.datetime.now().strftime('%S%f')[:-3]
        self.tick = (float(self.tick1) - float(self.tick2))
        if self.tick < 0:
            self.tick += 60000
        self.t3 += self.tick
        # 시작점
        dot1 = [self.result[self.ri][0], self.result[self.ri][1]]
        # 다음점
        dot2 = [self.result[self.ri + 1][0], self.result[self.ri + 1][1]]
        # 점 사이의 거리
        d2d_distance = haversine(dot1, dot2, unit=Unit.METERS)
        # 차량의 이동 거리
        if self.state == 0:
            md = 0
        else:
            md = float(self.__speed / 3600 * self.tick)
        rd = md - d2d_distance + self.rd
        line_check = self.ri
        while rd > 0:
            self.ri += 1
            if self.ri == len(self.result) - 3:
                self.ri = 0
                self.rd = 0
                self.re_dis = self.first_re_dis
            else:
                # 시작점
                dot1 = [self.result[self.ri][0], self.result[self.ri][1]]
                # 다음점
                dot2 = [self.result[self.ri + 1][0], self.result[self.ri + 1][1]]
                # 점 사이의 거리
                self.new_d2d_distance = haversine(dot1, dot2, unit=Unit.METERS)
                md = rd
                rd -= self.new_d2d_distance
                self.ch_while = 1
                self.re_dis = self.re_dis - self.new_d2d_distance
        if rd <= 0:
            dx = dot2[0] - dot1[0]
            dy = dot2[1] - dot1[1]
            if self.ch_while == 0:
                car_x = (md + self.rd) * dx / d2d_distance
                car_y = (md + self.rd) * dy / d2d_distance
            elif self.ch_while == 1:
                car_x = md * dx / self.new_d2d_distance
                car_y = md * dy / self.new_d2d_distance
            wgs_x = dot1[0] + car_x
            wgs_y = dot1[1] + car_y
            x = float((geo.wgs842tm(wgs_x, wgs_y)[0] - 232804.0) / 50)
            y = -18.98
            z = float((((geo.wgs842tm(wgs_x, wgs_y)[1]) - 420248) / 50) - 1.02 - 0.69)
            self.position = (x, y, z)
            if line_check == self.ri:
                self.rd += md
            else:
                self.rd = md
            self.rotation_y = self.result[self.ri][2]

        elif rd == 0:
            self.ri += 1
            dot1 = [self.result[self.ri][0], self.result[self.ri][1]]
            self.position = (geo.wgs842tm(dot1[0], dot1[1])[0] - 232804.0) / 50, -18.95, (
                        (((geo.wgs842tm(dot1[0], dot1[1])[1]) - 420248) / 50) - 1.02 - 0.69)
            self.rotation_y = self.result[self.ri][2]

        if self.t3 >= 100:
            self.t3 = 0
            # BSM 메시지 보내기
            [x, y, z] = self.position
            self.bsm_id = (1).to_bytes(1, byteorder="big", signed=True)
            self.bsm_CRC_16 = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Packet = (43).to_bytes(2, byteorder="big", signed=True)
            self.bsm_msgcnt = (self.msg_cnt).to_bytes(1, byteorder="big", signed=True)
            self.bsm_tmpid2 = (self.temp_id).to_bytes(4, byteorder="big", signed=True)
            self.bsm_DSecond = (0).to_bytes(2, byteorder="big", signed=True)
            # LAT, LONG 변환
            self.x3 = (x * 50) + 232804
            self.z3 = (z + 1.02 + 0.69) * 50 + 420248
            self.lat_car2 = int(round(geo.tm2wgs84(self.x3, self.z3)[0], 7) * 10000000)
            self.long_car2 = int(round(geo.tm2wgs84(self.x3, self.z3)[1], 7) * 10000000)
            self.bsm_lat2 = self.lat_car2.to_bytes(4, byteorder="big", signed=True)
            self.bsm_long2 = self.long_car2.to_bytes(4, byteorder="big", signed=True)
            self.bsm_ELev = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_PosAccy = (0).to_bytes(4, byteorder="big", signed=True)
            self.msg_speed_car2 = self.__speed / 3.6 / 0.02
            self.trans_speed_car2 = self.trans + int(self.msg_speed_car2)
            self.bsm_Trans_Speed2 = (self.trans_speed_car2).to_bytes(2, byteorder="big", signed=True)
            self.msg_heading_car2 = int(self.rotation_y / 0.0125)
            self.bsm_Heading2 = (self.msg_heading_car2).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Angle = (0).to_bytes(1, byteorder="big", signed=True)
            self.bsm_Acc = (0).to_bytes(7, byteorder="big", signed=True)
            self.bsm_Brake = (0).to_bytes(2, byteorder="big", signed=True)
            self.bsm_Size = (0).to_bytes(3, byteorder="big", signed=True)
            self.bsm = (
                    self.bsm_id + self.bsm_CRC_16 + self.bsm_Packet + self.bsm_msgcnt + self.bsm_tmpid2 
                    + self.bsm_DSecond + self.bsm_lat2 + self.bsm_long2 + self.bsm_ELev + self.bsm_PosAccy 
                    + self.bsm_Trans_Speed2 + self.bsm_Heading2 + self.bsm_Angle + self.bsm_Acc + self.bsm_Brake 
                    + self.bsm_Size)
            self.msg_cnt += 1
            if self.msg_cnt == 128:
                self.msg_cnt = 0
            self.client.sendto(self.bsm, self.client_addr)
            self.ui_client.sendto(self.bsm, self.ui_port)
            # pyqt로 로그 메시지 보내기
            msg = "[E_CAR >> ADS] MSG_TYPE : BSM, LAT : " + str(self.lat_car2) + ", LONG : " + str(
                self.long_car2) + ", HEADING : " + str(self.rotation_y) + ", SPEED : " + str(self.__speed)
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)
        if self.re_dis >= 0:
            edm_heading = 2
            try:
                if self.result[self.ri][2] - self.result[self.ri + 10][2] >= 2.5:
                    edm_heading = 4
                elif self.result[self.ri][2] - self.result[self.ri + 10][2] <= -2.5:
                    edm_heading = 3
            except BaseException:
                pass
            edm_msg = struct.pack('>B H H I H B', 7, 0, 12, self.temp_id, edm_heading, int(self.re_dis))
            self.client.sendto(edm_msg, self.client_addr)
            self.ui_client.sendto(edm_msg, self.ui_port)
            msg = "[E_CAR >> ADS] MSG_TYPE : EDM, 남은 주행 거리 = " + str(self.re_dis) + "m"
            self.qt_log_server.sendto(msg.encode(), self.qt_iport)
        self.ch_while = 0

    @property
    def speed(self):
        """ speed """
        return self.__speed

    @speed.setter
    def speed(self, s):
        """ set speed """
        self.__speed = s

    def key_control(self):
        """ keyboard control """
        if held_keys["r"]:  # 포지션 리셋
            print("초기 위치로 설정됩니다.")
            self.ri = 0
            self.rd = 0
            self.re_dis = self.first_re_dis
        elif held_keys["d"]:
            print("다시 주행을 시작합니다.")
            self.state = 1
        elif held_keys["s"]:
            print("차량의 움직임을 멈춥니다.")
            self.state = 0

    def case_d(self):
        """ case d simulation car location """
        self.re_dis = 0
        self.re_count = 0
        with open("convert_d.txt", "r") as fp:
            j = 0
            ri = 0
            for i in fp.readlines():
                tmp = i.split(",")
                tmp[2] = tmp[2].replace("\n", "")

                if j == 0:
                    self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), 0.0])
                    ri += 1
                    j += 1

                else:
                    if 1 <= ri:
                        first = (float(self.result[ri - 1][0]), float(self.result[ri - 1][1]))
                        second = (float(tmp[0]) / 10000000, float(tmp[1]) / 10000000)
                        c = haversine(first, second, unit=Unit.METERS)
                        self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), c])
                        ri += 1
        for i in self.result:
            self.re_dis += float(self.result[self.re_count][3])
            self.re_count += 1
        self.first_re_dis = self.re_dis

    def case_e(self):
        """ case e simulation car location """
        self.re_dis = 0
        self.re_count = 0
        with open("convert_e.txt", "r") as fp:
            j = 0
            ri = 0
            for i in fp.readlines():
                tmp = i.split(",")
                tmp[2] = tmp[2].replace("\n", "")

                if j == 0:
                    self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), 0.0])
                    ri += 1
                    j += 1

                else:
                    if 1 <= ri:
                        first = (float(self.result[ri - 1][0]), float(self.result[ri - 1][1]))
                        second = (float(tmp[0]) / 10000000, float(tmp[1]) / 10000000)
                        c = haversine(first, second, unit=Unit.METERS)
                        self.result.append([float(tmp[0]) / 10000000, float(tmp[1]) / 10000000, float(tmp[2]), c])
                        ri += 1
        for i in self.result:
            self.re_dis += float(self.result[self.re_count][3])
            self.re_count += 1
        self.first_re_dis = self.re_dis


class curb(Entity):
    """ curb road """
    def __init__(self, position=(0, 0, 0), rotation_y=-100):
        super().__init__(
            model='objects/road2/curb.obj',
            collider='mesh',
            texture='objects/road2/curb.jpg',
            scale=0.018,
            position=position,
            rotation_y=rotation_y
        )


class straight(Entity):
    """ straight road """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.019, visible=True):
        super().__init__(
            model='objects/road2/str.obj',
            collider='mesh',
            texture='objects/road2/str.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y,
            visible=visible
        )


class l_short_straight(Entity):
    """ straight road """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.019):
        super().__init__(
            model='objects/road2/short_R.obj',
            collider='mesh',
            texture='objects/road2/str.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class r_short_straight(Entity):
    """ straight road """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.019):
        """ init """
        super().__init__(
            model='objects/road2/short_L.obj',
            collider='mesh',
            texture='objects/road2/str.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class long_none_straight(Entity):
    """ long_none """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.019):
        super().__init__(
            model='objects/road2/long_none.obj',
            collider='mesh',
            texture='objects/road2/str.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class curb_side(Entity):
    """ curb side """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=1):
        """ init """
        super().__init__(
            model='objects/road2/curb_side.obj',
            collider='mesh',
            texture='objects/road/sidewalk.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class r_long_straight(Entity):
    """ straight """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.019):
        """ init """
        super().__init__(
            model='objects/road2/str.obj',
            collider='mesh',
            texture='objects/road2/str.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class pillar(Entity):
    """ pillar """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.0003):
        """ init """
        super().__init__(
            model='objects/road2/pillar.obj',
            collider='mesh',
            color=color.gray,
            scale=scale,
            position=position,
            rotation_y=rotation_y,
            # texture = 'objects/road2/str.jpg',
        )


class straight_v2(Entity):
    """ straight """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.019):
        """ init """
        super().__init__(
            model='objects/road2/4wayobj.obj',
            collider='mesh',
            texture='objects/road2/4wayobj.png',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class road_nomal(Entity):
    """ road """
    def __init__(self, position=(0, 0, 0), rotation_y=0, scale=(0.55, 1, 0.55)):
        """ init """
        super().__init__(
            model='plane',
            collider='mesh',
            texture='objects/road2/road_texture.jfif ',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class curb_line_1(Entity):
    """ curb """
    def __init__(self, position=(0, 0, 0), color=color.white):
        """ init """
        super().__init__(
            model='objects/road/ttttt.stl',
            scale=0.12,
            position=position,
            rotation=(90, -11, 00),
            color=color
        )


class test11(Entity):
    """ tjunction """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__(
            model='objects/road/Tjunction.obj',
            collider='mesh',
            texture='objects/road/Tjunction.mtl',
            scale=0.1,
            position=position
        )


class tree1(Entity):
    """ tree """
    def __init__(self, position=(0, 0, 0)):
        super().__init__(
            model='objects/tree/Tree2.obj',
            collider='mesh',
            texture='objects/tree/Branches0018_1_S.png',
            scale=0.1,
            position=position
        )


class menu_car1(Entity):
    """ solo car img """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__(
            model='objects/car/solo_car.obj',
            collider='mesh',
            # texture = 'objects/car/APC_Pacer_003.png',
            texture='objects/car/white.png',
            scale=1,  # 원래 0.05
            position=position,
        )

    async def update(self):
        """ update """
        self.rotation += (0, 0.03, 0)


class road_Box(Entity):
    """ road_box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__(
            model="objects/road/road.obj",
            collider='mesh',
            texture='objects/road/road texture.dds',
            scale=1,
            position=position
        )


class road_2Box(Entity):
    """ road_box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__(
            model="cube",
            collider='mesh',
            texture='objects/road/Boulevard.png',
            scale=0.1,
            position=position,
            rotation_y=100
        )

class sidewalk_Box(Entity):
    """ sidewalk """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.2):
        """ init """
        super().__init__(
            model="cube",
            collider='mesh',
            texture='objects/road/sidewalk.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class fance(Entity):
    """ fence """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.1):
        """ init """
        super().__init__(
            model="objects/road2/FENCE 2.obj",
            collider='mesh',
            texture='objects/road2/FENCE 1 (1).jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class streetlamp(Entity):
    """ street lamp """
    def __init__(self, position=(0, 0, 0), rotation_y=-100, scale=0.06):
        """ init """
        super().__init__(
            model="objects/road2/STREETLAMP.obj",
            collider='mesh',
            texture='objects/road2/STREETLAMP VER 2.jpg',
            scale=scale,
            position=position,
            rotation_y=rotation_y
        )


class road_small_Box(Entity):
    """ road box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(0, 0, 0.25)
        self.scale = 0.5


class road_2small_Box(Entity):
    """ road box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(0, 0, 1)
        self.scale = 0.25


class white_Box(Entity):
    """ white box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(0, 0, 1)


class white_small_Box(Entity):
    """ white box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(0, 0, 1)
        self.scale = 0.5


class yellow_Box(Entity):
    """ yellow box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(60, 1, 1)


class yellow_small_Box(Entity):
    """ yellow box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(60, 1, 1)
        self.scale = 0.5


class green_Box(Entity):
    """ green box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.collider = 'box'
        self.color = color.color(120, 1, 1)


class pink_Box(Entity):
    """ pink box """
    def __init__(self, position=(0, 0, 0)):
        """ init """
        super().__init__()
        self.position = position
        self.model = 'cube'
        self.color = color.color(330, 1, 1)


class column_road():
    """ road """
    def __init__(self, posx=0, posy=0, posz=0, rd=40, la=3):
        """ init """
        for x in range(posx, posx + rd):
            for z in range(posz - la * 3, posz + la * 3):
                if z == posz:
                    yellow_Box(position=(x, posy, z))  # 가운데 라인
                elif z == posz - 4:
                    if x % 4 == 0:
                        road_Box(position=(x, posy, z))  # 오른쪽 점선
                    else:
                        white_Box(position=(x, posy, z))
                elif z == posz + 4:
                    if x % 4 == 0:
                        road_Box(position=(x, posy, z))  # 왼쪽 점선
                    else:
                        white_Box(position=(x, posy, z))
                elif z == posz - la * 3:
                    yellow_Box(position=(x, posy, z))  # 양끝 라인
                elif z == posz + la * 3 - 1:
                    yellow_Box(position=(x, posy, z))
                else:
                    road_Box(position=(x, posy, z))
