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


""" Main windows"""
import sys
from PyQt5.QtWidgets import *

import pyautogui
import struct
from graph_chart import *

"""
app = QApplication(sys.argv)

root = MyWindow()
root.show()

test2 = MyWindow()
test2.show()
test2.close()
sys.exit(app.exec_())

"""

class MyApp(QMainWindow):
    """ Main windows """
    def __init__(self):
        """ init """
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)
        size_x , size_y = 800, 800
        width, height = pyautogui.size()
        self.setGeometry(width/80+width/1.5, height/8, (width*0.48)/1.5,(height)/1.5)


    def initUI(self):
        """ init UI, simulation windows & log/chart windows """
        ads_chart = ads_speed_chart()
        car1_chart = car1_speed_chart()
        car2_chart = car2_speed_chart()
        data_wd = log_wiget()

        impMenu = QMenu('업데이트 속도 변경', self)
        impAct1 = QAction('느리게', self)
        impAct2 = QAction('보통', self)
        impAct3= QAction('빠르게', self)
        impMenu.addAction(impAct1)
        impMenu.addAction(impAct2)
        impMenu.addAction(impAct3)
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        ########################################################

        menu = self.menuBar()
        menu_file = menu.addMenu("File")
        menu_edit = menu.addMenu("Edit")
        menu_sample = menu.addMenu("Sample")

        menu_file.addMenu(impMenu)
        menu_file.addAction(exitAction)

        self.chartlayout = QVBoxLayout()
        self.chartlayout.addWidget(ads_chart,100)
        self.chartlayout.addWidget(car1_chart, 100)
        self.chartlayout.addWidget(car2_chart, 100)

        self.up_frame = QFrame()
        self.up_frame.setLayout(self.chartlayout)

        layout = QVBoxLayout()
        layout.addWidget(self.up_frame, 70)
        layout.addWidget(data_wd, 50)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Etri_1.0')

        # ADS 속도 그래프
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(ads_chart.ads_plot_data)
        self.timer.start()
        # CAR1 속도 그래프
        self.timer2 = QtCore.QTimer()
        self.timer2.setInterval(50)
        self.timer2.timeout.connect(car1_chart.car1_plot_data)
        self.timer2.start()
        # CAR2,E_car 속도 그래프
        self.timer3 = QtCore.QTimer()
        self.timer3.setInterval(50)
        self.timer3.timeout.connect(car2_chart.car2_e_plot_data)
        self.timer3.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())