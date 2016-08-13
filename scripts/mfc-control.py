#!/usr/bin/python2
#
# tracer gas injection script
#
# Patrick O'Keeffe

from __future__ import print_function

import os, os.path as osp
import serial

import time
from threading import Timer

import logging

import paho.mqtt.client as paho


################## USER-DEFINED VALUES ##################
LOGGING_DIRECTORY = '/var/log/mfc/'
MESSAGES_FILENAME = 'mfc.log' # cumulative
DATALOG_FILENAME  = 'mfc' # rotated daily to mfc.YYYYMMDD.tsv

INJECT_SCALE = 100  # int {2-100}, percent MFC open
INJECT_TIME = 120    # int {>0}, duration in seconds

BROKER_ADDR = '10.1.1.4'
BROKER_PORT = '1883'
REPORT_TOPIC = 'home/tracer/mfc/state'
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

#### MQTT integration
client = paho.Client()
client.connect(BROKER_ADDR, BROKER_PORT)
client.loop_start()


msg.info("Starting tracer injection routine...")

TP = 0 # tank pressure
SP = 0 # set point
ON = 0 # "is running" flag
def poll_mfc():
    global TP; global SP # i know, i know..
    mfc.write("A\r")
    time.sleep(0.010)
    record = mfc.read(80)
    try:
        (_, P_air, T_air, F_vol, F_mass, F_sp, gas) = record.split()
        log.info('\t'.join([P_air, T_air, F_vol, F_mass, F_sp, gas]))
        TP, SP = float(P_air), float(F_sp)

        client.publish(REPORT_TOPIC,
            ('{"tstamp": %.2f, "injecting": %s, "inlet_P": %s}' %
             (time.time(), ON, TP)),
            qos=1, retain=True)
        #msg.info('%s %s' % (TP, SP))
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
mfc =  serial.Serial('/dev/mfc', 19200, timeout=0.10)

msg.info("Asserting control of MFC...")
mfc.write("*@=A\r")

msg.info("Starting data logger...")
mfc_logger = TimedAsker(1, poll_mfc) # auto-starts
while (TP < 0.01):
    sleep(1)

msg.info("Checking tank pressure...")
min_tank_press = 20 # psia
if TP < min_tank_press:
   msg.info("Insufficient pressure: %s psia [warning: graceful shutdown not implemented]" % TP)
   # TODO FIXME

ON = 1 # let the injection begin

msg.info("Waiting for stable readings...")
time.sleep(3) # typ. misses 1st second

msg.info("Opening MFC to %i%%..." % INJECT_SCALE)
retries = 5
for i in range(retries):
    mfc.write('A%i\r' % (64000*INJECT_SCALE/100.0))
    if (SP > 0):
        break
    time.sleep(1.5)
    msg.info("Retrying (%s of %s attempts)..." % (i+1, retries))

msg.info("Injecting for %i seconds..." % INJECT_TIME)
time.sleep(INJECT_TIME)

msg.info("Closing MFC valve...")
for i in range(retries):
    mfc.write("A0\r")
    if (SP < 0.1):
        break
    time.sleep(1.5)
    msg.info("Retrying (%s of %s attempts)..." % (i+1, retries))

ON = 0 # injection is over

msg.info("Waiting for stable readings...")
time.sleep(5)

msg.info("Saving log files...")
mfc_logger.stop()
time.sleep(1)

msg.info("Done.")

mfc.close()

client.loop_stop()
