#!/usr/bin/python2
#
# Monitor current switch, record to file and report to dashboard
#
# Patrick O'Keeffe <pokeeffe@wsu.edu>

from __future__ import print_function

import os, os.path as osp
import time
import logging
from logging import StreamHandler

import paho.mqtt.client as paho
import RPi.GPIO as GPIO

#### read config file
import ConfigParser as configparser
c = configparser.ConfigParser()
c.read('/etc/tracer/switch-logger.conf')

DETECT_PIN = int(c.get('main', 'pin'))
LOGDIR = c.get('logging', 'logdir')
LOGFILE = c.get('logging', 'logfile')
MQTT_SERVER = c.get('mqtt', 'broker_ip')
MQTT_PORT = c.get('mqtt', 'broker_port')
REPORT_TOPIC = c.get('mqtt', 'report_topic')

#### logging setup
log_path = osp.join(LOGDIR, LOGFILE)
try:
    os.makedirs(LOGDIR)
except OSError:
    if not osp.isdir(LOGDIR):
        raise

# HINT force logging to include UTC offset
# XXXX doesn't work for partial-hour offsets
_Z = '{:+03d}00'.format(-time.timezone/3600)
tsvfmt = '%(asctime)s.%(msecs)03d{}\t%(message)s'.format(_Z)

log_file = logging.FileHandler(log_path)
log_file.setFormatter(logging.Formatter(tsvfmt,
                                        datefmt='%Y-%m-%dT%H:%M:%S%z'))
log = logging.getLogger('current-switch')
log.setLevel(logging.INFO)
log.addHandler(log_file)

log.addHandler(logging.StreamHandler()) # for debugging

#### switch detection
GPIO.setmode(GPIO.BCM)
GPIO.setup(DETECT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#### MQTT setup
def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code %d." % (rc))

def on_publish(client, userdata, mid):
    pass

client = paho.Client()
client.on_connect = on_connect
client.on_publish = on_publish
client.connect(MQTT_SERVER, MQTT_PORT)
client.loop_start()

report = '{"tstamp": %.2f, "is_on": %s}'


#### run-time loop
while(True):
    try:
        state = GPIO.input(DETECT_PIN)
        is_on = int(state == GPIO.LOW)

        # record to file and stdout
        log.info('\t'.join([str(is_on), 'on' if is_on else 'off']))

        # report to dashboard
        client.publish(REPORT_TOPIC, report % (time.time(), is_on),
                       qos=1, retain=True)

        # stand-by waiting for change
        GPIO.wait_for_edge(DETECT_PIN, GPIO.BOTH, bouncetime=200)
    except KeyboardInterrupt, SystemExit:
        GPIO.cleanup()
        client.loop_stop()

