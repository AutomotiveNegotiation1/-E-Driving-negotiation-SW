# Copyright 2022 ETRI. All rights reserved. 
# License-identifier: MIT
# kwmin92@etri.re.kr, yssong00@etri.re.kr

""" log """
import os
import logging
import sys

LOG_FILE_PATH = "/var/tmp/auto-car/auto-car-log"
loggers = dict()
DEFAULT_FORMATTER = '%(asctime)s %(name)s %(levelname)s %(message)s'


def getLogger(name='unknown'):
    """ get logger """
    if loggers.get(name, None) == None:
        # default file logging
        if os.path.exists(os.path.dirname(LOG_FILE_PATH)) == False:
            os.makedirs(os.path.dirname(LOG_FILE_PATH))
            os.chmod(os.path.dirname(LOG_FILE_PATH), 0o777)
            open(LOG_FILE_PATH, "w+").close()
            os.chmod(LOG_FILE_PATH, 0o666)
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                datefmt='%m-%d-%Y %H:%M',
                filename=LOG_FILE_PATH,
                filemode='a')

        logger = logging.getLogger(name)
        '''
        hdlr = logging.FileHandler(LOG_FILE_PATH)
        hdlr.setLevel(logging.INFO)
        formatter = logging.Formatter(DEFAULT_FORMATTER)
        hdlr.setFormatter(formatter)
        '''
        # add stdout logging with INFO level
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)

        loggers[name] = logger

    return loggers.get(name)
