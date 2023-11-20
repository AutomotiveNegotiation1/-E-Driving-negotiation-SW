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

""" speed chart and log  windows """

import datetime
import struct
from PyQt5.QtWidgets import *
from pyqtgraph import *
from socket import *
import pyqt_server

port = 31252
test_car1_speed = None
test_car2_speed = None

# QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

class ads_speed_chart(QtWidgets.QMainWindow):
    """
    speed_chart windows (ADS CAR)
    """
    def __init__(self, *args, **kwargs):
        """ init """
        super(ads_speed_chart, self).__init__(*args, **kwargs)

        self.graphWidget = PlotWidget()
        self.graphWidget.setYRange(0,100)
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(100))  # 100 time points
        self.y = list(range(100))  # [randint(0,100) for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground('w')

        pen = mkPen(color=(0, 0, 255)) #파란색으로 색칠하기
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)

    def ads_plot_data(self):
        """ ads speed data graph """
        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(pyqt_server.ads_speed) # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.


class car1_speed_chart(QtWidgets.QMainWindow):
    """
    speed_chart windows (Simul CAR1)
    """
    def __init__(self, *args, **kwargs):
        """ init """
        super(car1_speed_chart, self).__init__(*args, **kwargs)

        self.graphWidget = PlotWidget()
        self.graphWidget.setYRange(0, 100)
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(100))  # 100 time points
        self.y = list(range(100))  # [randint(0,100) for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground('w')

        pen = mkPen(color=(255, 212, 0)) #노란색으로 색칠하기

        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)


    def car1_plot_data(self):
        """ simul CAR1 speed data graph """

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(pyqt_server.car1_speed) # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.

class car2_speed_chart(QtWidgets.QMainWindow):
    """
    speed_chart windows (Simul CAR2)
    """
    def __init__(self, *args, **kwargs):
        """ init """
        super(car2_speed_chart, self).__init__(*args, **kwargs)

        self.graphWidget = PlotWidget()
        self.graphWidget.setYRange(0, 100)
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(100))  # 100 time points
        self.y = list(range(100))  # [randint(0,100) for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground('w')

        pen = mkPen(color=(0,255,0)) # 녹색으로 색칠하기

        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)

    def car2_e_plot_data(self):
        """ simul CAR2 speed data graph """
        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(pyqt_server.car2_speed) # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.

class log_wiget(QWidget):
    """
    Log windows (ADS & Simul CAR Send/Receive log)
    """
    def __init__(self):
        """ init """
        super().__init__()

        self.s = pyqt_server.ServerSocket(self)
        self.s.start()
        self.initUI()

    def initUI(self):
        """ init UI """

        # 서버 설정 부분
        ipbox = QHBoxLayout()
        self.i = 0
        gb = QGroupBox('로그')
        ipbox.addWidget(gb)

        box = QHBoxLayout()

        self.btn = QPushButton('Logging')
        self.btn.setCheckable(True)
        self.btn.toggled.connect(self.toggleButton)
        box.addWidget(self.btn)
        #
        gb.setLayout(box)

        self.f = open(r"log_file.txt","a")
        # 채팅창 부분
        infobox = QHBoxLayout()
        gb = QGroupBox('logger')
        infobox.addWidget(gb)

        box = QVBoxLayout()

        self.msg = QListWidget()
        box.addWidget(self.msg)

        gb.setLayout(box)

        # 전체 배치
        vbox = QVBoxLayout()
        vbox.addLayout(ipbox)
        vbox.addLayout(infobox)
        self.setLayout(vbox)

        self.show()

    def toggleButton(self, state):
        """ button toggle Logging & Logging Stop"""
        if state:
            # ip = self.ip.text()
            # port = self.port.text()
            self.s.stop()
            self.btn.setText('Logging Stop')
            # self.msg.clear()
        else:
            self.s.start()
            self.btn.setText('Logging')
            self.msg.clear()

    def updateClient(self, addr, isConnect=False):
        """ update Client """
        row = self.guest.rowCount()

        if isConnect:
            self.guest.setRowCount(row + 1)
            self.guest.setItem(row, 0, QTableWidgetItem(addr[0]))
            self.guest.setItem(row, 1, QTableWidgetItem(str(addr[1])))
        else:
            for r in range(row):
                ip = self.guest.item(r, 0).text()  # ip
                port = self.guest.item(r, 1).text()  # port
                if addr[0] == ip and str(addr[1]) == port:
                    self.guest.removeRow(r)
                    break

    def updateMsg(self, msg):
        """ update log msg """
        self.msg.addItem(QListWidgetItem(msg))
        self.msg.setCurrentRow(self.msg.count() - 1)
        self.f.writelines(msg)
        self.f.writelines("\n")
        if self.msg.count() > 350:
            self.msg.clear()

    def sendMsg(self):
        """ send msg logging """
        if not self.s.bListen:
            self.sendmsg.clear()
            return
        sendmsg = self.sendmsg.text()
        self.updateMsg(sendmsg)
        print(sendmsg)
        self.s.send(sendmsg)
        self.sendmsg.clear()

    def clearMsg(self):
        """ clear msg logging """
        self.msg.clear()

    def closeEvent(self, e):
        """ close event """
        self.s.stop()

    def contol_wd(self):
        """ control windows """
        pass
