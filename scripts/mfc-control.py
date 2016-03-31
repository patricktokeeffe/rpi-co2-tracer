#!/usr/bin/python
#
# tracer gas injection script
#
# Patrick O'Keeffe

from __future__ import print_function

import os, os.path as osp
import serial

from time import sleep
from threading import Timer

import logging


################## USER-DEFINED VALUES ##################
LOGGING_DIRECTORY = '/var/log/mfc/'
MESSAGES_FILENAME = 'mfc.log' # cumulative
DATALOG_FILENAME  = 'mfc' # rotated daily to mfc.YYYYMMDD.tsv

INJECT_SCALE = 100  # int {2-100}, percent MFC open
INJECT_TIME = 120    # int {>0}, duration in seconds
#########################################################


try:
    os.makedirs(LOGGING_DIRECTORY)
except OSError:
    if not osp.isdir(LOGGING_DIRECTORY):
        raise

# setup logging narrative messages to file
msglog = logging.FileHandler(osp.join(LOGGING_DIRECTORY, MESSAGES_FILENAME))
msglog.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d\t%(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
                            # http://stackoverflow.com/a/7517430/2946116
msg = logging.getLogger(__name__+".messages")
msg.setLevel(logging.INFO)
msg.addHandler(msglog)
msg.addHandler(logging.StreamHandler()) # +console/stderr

# setup logging tab-separated data to file
datlog = logging.FileHandler(osp.join(LOGGING_DIRECTORY, DATALOG_FILENAME))
datlog.setFormatter(logging.Formatter('%(asctime)s\t%(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
log = logging.getLogger(__name__+".data")
log.setLevel(logging.INFO)
log.addHandler(datlog)

msg.info("Starting tracer injection routine...")
#log.info('\t'.join(['1', '2', '3']))
#import sys; sys.exit()

def poll_mfc():
    mfc.write("A\r")
    sleep(0.010)
    record = mfc.read(80)
    try:
        (_, P_air, T_air, F_vol, F_mass, F_sp, gas) = record.split()
        #print('\t'.join([P_air, T_air, F_vol, F_mass, F_sp, gas]))
        log.info('\t'.join([P_air, T_air, F_vol, F_mass, F_sp, gas]))
    except:
        pass

# http://stackoverflow.com/a/13151299/2946116
class TimedAsker(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

msg.info("Opening serial connection to MFC...")
mfc =  serial.Serial('/dev/mfc', 19200, timeout=0.050)

msg.info("Asserting control of MFC...")
mfc.write("*@=A\r")

msg.info("Starting data logger...")
mfc_logger = TimedAsker(1, poll_mfc) # auto-starts

msg.info("Waiting for stable readings...")
sleep(6) # typ. missing 1st second

msg.info("Opening MFC to %i%%..." % INJECT_SCALE)
mfc.write("A%i\r" % (64000 *INJECT_SCALE/100.0))

msg.info("Injecting for %i seconds..." % INJECT_TIME)
sleep(INJECT_TIME)

msg.info("Closing MFC valve...")
mfc.write("A0\r")

msg.info("Waiting for stable readings...")
sleep(5)

msg.info("Saving log files...")
mfc_logger.stop()

msg.info("Done.")


