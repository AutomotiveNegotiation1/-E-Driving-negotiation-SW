# Copyright 2022 ETRI. All rights reserved. 
# License-identifier: MIT
# kwmin92@etri.re.kr, yssong00@etri.re.kr

# Function Utilities
""" utility """
from collections import deque

def generate_speed():
    """ speed """
    #genrate speed caption and values
    last_speed = 0.3
    init_speed = 0.1
    ret_speed = {}
    while init_speed <= last_speed:        
        speed_caption = 'Speed: {}'.format(init_speed)
        ret_speed[speed_caption] = init_speed
        init_speed = init_speed + 0.01
        init_speed = round(init_speed,2)
        
    return ret_speed    
    
        
class RingBuffer(deque):
    """
    inherits deque, pops the oldest data to make room
    for the newest data when size is reached
    """
    def __init__(self, size):
        """ init """
        deque.__init__(self)
        self.size = size
        
    def full_append(self, item):
        """ append """
        deque.append(self, item)
        # full, pop the oldest item, left most item
        self.popleft()
        
    def append2(self, item):
        """ append2 """
        deque.append(self, item)
        # max size reached, append becomes full_append
        if len(self) == self.size:
            self.append2 = self.full_append
    
    def get(self):
        """returns a list of size items (newest items)"""
        return list(self)    
