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

""" Main for Driving Negotiation Simulation"""

import sys
import os
import pyautogui
import ursina
import pyqtgraph
import PyQt5

from ursina import *
from main_menu import MainMenu
from PyQt5.QtWidgets import *

window_size = pyautogui.size()

Text.default_resolution = 1080 * Text.size
app = [Ursina(), QApplication(sys.argv)]

window.title = "Etri_1.0"
window.borderless = False
window.fullscreen = False
window.show_ursina_splash = True
window.cog_button.disable()

width, height = window_size

window.size = (width/ 1.5, height/1.5)
window.position = Vec2(width/80, height/8)

main_menu = MainMenu()

app[0].run()


