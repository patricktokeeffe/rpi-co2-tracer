#!/usr/bin/python2

# Get temperature from Adafruit MAX31855 breakout board and do stuff
#
# Patrick O'Keeffe <pokeeffe@wsu.edu>
# Laboratory for Atmospheric Research at Washington State University
#
# see <https://learn.adafruit.com/max31855-thermocouple-python-library>

from __future__ import print_function

import os, os.path as osp
import time
import math
import logging
from logging.handlers import TimedRotatingFileHandler

import Adafruit_MAX31855.MAX31855 as MAX

import paho.mqtt.client as paho

#### read config data
import ConfigParser as configparser
c = configparser.ConfigParser()
c.read('/etc/tracer/typek-logger.conf')

CLK = int(c.get('main', 'CLK'))
CS = int(c.get('main', 'CS'))
DO = int(c.get('main', 'DO'))
interval = int(c.get('main', 'interval'))
logdir = c.get('main', 'logdir')
logfile = c.get('main', 'logfile')
broker_addr = c.get('mqtt', 'broker_addr')
broker_port = c.get('mqtt', 'broker_port')
report_topic = c.get('mqtt', 'report_topic')

#### logging setup
try:
    os.makedirs(logdir)
except OSError:
    if not osp.isdir(logdir):
        raise

# HINT force logging to include UTC offset
# XXXX doesn't work with partial-hour offsets
_Z = '{:+03d}00'.format(-time.timezone/3600)

log_path = osp.join(logdir, logfile)
log_handler = TimedRotatingFileHandler(log_path, when='midnight')
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(message)s',
                                           datefmt='%Y-%m-%dT%H:%M:%S'+_Z))
log_handler.suffix = '%Y-%m-%d.tsv'
log = logging.getLogger('typek-logger')
log.setLevel(logging.INFO)
log.addHandler(log_handler)

log.addHandler(logging.StreamHandler()) # for debugging

#### MQTT integration
def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code %d." % (rc))

client = paho.Client()
client.on_connect = on_connect
client.connect(broker_addr, broker_port)
client.loop_start()


sensor = MAX.MAX31855(CLK, CS, DO)
while True:
    try:
        tmpr, ltmpr = sensor.readTempC(), sensor.readLinearizedTempC()

        log.info('\t'.join(['{:0.2F}'.format(tmpr),
                            '{:0.2F}'.format(ltmpr)]))

        if not math.isnan(tmpr):
            client.publish(report_topic,
                           ('{"tstamp": %.2f, "T": %s}' %
                            (time.time(), tmpr)),
                           qos=1, retain=True)

        time.sleep(interval)
    except (KeyboardInterrupt, SystemExit):
        client.loop_stop()
        raise
    except:
        pass
