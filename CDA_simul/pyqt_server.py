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

""" pyqt server """
from threading import Thread
from socket import *
from PyQt5.QtCore import *
from graph_chart import *
import struct
ads_speed = car2_speed = car1_speed = 0

class ServerSocket(QObject):
    """ server socket """
    global send_msg
    update_signal = pyqtSignal(tuple, bool)
    recv_signal = pyqtSignal(str)

    def __init__(self, parent):
        """ init """
        super().__init__()
        self.parent = parent
        self.bListen = False
        self.clients = []
        self.ip = []
        self.threads = []

        self.update_signal.connect(self.parent.updateClient)
        self.recv_signal.connect(self.parent.updateMsg)

    def __del__(self):
        """ stop """
        self.stop()

    def start(self):
        """ start """
        self.server = socket(AF_INET, SOCK_DGRAM)
        self.client = socket(AF_INET, SOCK_DGRAM)

        try:
            self.server.bind(("localhost", 55555))
        #except Exception as e:
        except BaseException:
            #print('Bind Error : ', e)
            print('Bind Error : ')
            return False
        else:
            self.bListen = True
            self.t = Thread(target=self.receive, args=())
            self.t.start()

        return True

    def stop(self):
        """ logging stop """
        self.bListen = False
        if hasattr(self, 'server'):
            self.server.close()
            print('Logging stop')

    def receive(self):
        """ receive msg """
        global ads_speed, car2_speed, car1_speed
        while True:
            try:
                msg, self.addr = self.server.recvfrom(90000)

            except BaseException:
                print('Logging stop')
                break
            else:
                if msg:
                    if msg.decode()[:5] == "speed":
                        ads_speed = int(msg.decode()[5:8])
                        car1_speed = int(msg.decode()[8:11])
                        car2_speed = int(msg.decode()[11:14])
                    else:
                        self.recv_signal.emit(str(msg.decode()))

    def send(self, test_msg):
        """ send msg """
        try:
            self.server.sendto(test_msg, self.addr)

        #except Exception as e:
        except BaseException:
            #print('Send() Error : ', e)
            print('Send() Error : ')

    def removeClient(self, client):
        """ disconnect client """
        # find closed client index
        idx = -1
        for k, v in enumerate(self.clients):
            if v == client:
                idx = k
                break

        del (self.threads[idx])
        self.update_signal.emit(False)
        self.resourceInfo()

    def removeAllClients(self):
        """ socket close """
        for c in self.clients:
            c.close()

        for addr in self.ip:
            self.update_signal.emit(addr, False)

        self.ip.clear()
        self.clients.clear()
        self.threads.clear()

        self.resourceInfo()

    def resourceInfo(self):
        """ resource Info """
        print('Number of Client ip\t: ', len(self.ip))
        print('Number of Client socket\t: ', len(self.clients))
        print('Number of Client thread\t: ', len(self.threads))
