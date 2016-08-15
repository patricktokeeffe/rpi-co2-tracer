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

#### read config file
import ConfigParser as configparser
c = configparser.ConfigParser()
c.read('/etc/tracer/mfc-control.conf')

serial_port = c.get('main', 'serial_port')
serial_baud = c.getint('main', 'serial_baud')
inject_rate = c.getint('main', 'inject_rate')
inject_time = c.getint('main', 'inject_time')
log_dir = c.get('logging', 'log_dir')
msg_file = c.get('logging', 'msg_file')
log_file = c.get('logging', 'log_file')
broker_addr = c.get('mqtt', 'broker_addr')
broker_port = c.get('mqtt', 'broker_port')
report_topic = c.get('mqtt', 'report_topic')

#### logging setup
try:
    os.makedirs(log_dir)
except OSError:
    if not osp.isdir(log_dir):
        raise

# HINT force logging to include UTC offset
# XXXX doesn't work with partial-hour offsets
_Z = '{:+03d}00'.format(-time.timezone/3600)
msgfmt = '%(asctime)s.%(msecs)03d{}\t%(message)s'.format(_Z)

# setup logging narrative messages to file
msglog = logging.FileHandler(osp.join(log_dir, msg_file))
msglog.setFormatter(logging.Formatter(msgfmt,
                                      datefmt='%Y-%m-%d %H:%M:%S'))
                            # http://stackoverflow.com/a/7517430/2946116
msg = logging.getLogger(__name__+".messages")
msg.setLevel(logging.INFO)
msg.addHandler(msglog)
msg.addHandler(logging.StreamHandler()) # +console/stderr

# setup logging tab-separated data to file
datlog = logging.FileHandler(osp.join(log_dir, log_file))
datlog.setFormatter(logging.Formatter('%(asctime)s\t%(message)s',
                                      datefmt='%Y-%m-%dT%H:%M:%S'+_Z))
log = logging.getLogger(__name__+".data")
log.setLevel(logging.INFO)
log.addHandler(datlog)

#### MQTT integration
client = paho.Client()
client.connect(broker_addr, broker_port)
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

        client.publish(report_topic,
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
mfc =  serial.Serial(serial_port, serial_baud, timeout=0.10)

msg.info("Asserting control of MFC...")
mfc.write("*@=A\r")

msg.info("Starting data logger...")
mfc_logger = TimedAsker(1, poll_mfc) # auto-starts

msg.info("Waiting for data...")
for i in range(10):
    time.sleep(1)
    if (TP > 1): # meaning 'valid data received'
        break

if (TP < 20):
    if (TP < 1):
        msg.info("Timed out! Is MFC over pressure?")
    else:
        msg.info("Low pressure! PV: %s psia, SP: 20-30 psia" % TP)
    msg.info("Aborting...")
    mfc_logger.stop()
    client.loop_stop()
    import sys
    sys.exit()

ON = 1 # let the injection begin

msg.info("Waiting for stable readings...")
time.sleep(3) # typ. misses 1st second

msg.info("Opening MFC to %i%%..." % inject_rate)
retries = 5
for i in range(retries):
    mfc.write('A%i\r' % (64000*inject_rate/100.0))
    if (SP > 0):
        break
    time.sleep(1.5)
    msg.info("Retrying (%s of %s attempts)..." % (i+1, retries))

msg.info("Injecting for %i seconds..." % inject_time)
time.sleep(inject_time)

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
