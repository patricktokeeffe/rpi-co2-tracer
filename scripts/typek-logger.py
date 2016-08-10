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
import logging
from logging.handlers import TimedRotatingFileHandler

### FIXME why isn't this handler under `logging.handlers`?
from logging import StreamHandler
###

import Adafruit_MAX31855.MAX31855 as MAX

import ConfigParser as configparser
c = configparser.ConfigParser()
c.read('/etc/tracer/typek-logger.conf')

CLK = int(c.get('main', 'CLK'))
CS = int(c.get('main', 'CS'))
DO = int(c.get('main', 'DO'))
interval = int(c.get('main', 'interval'))
logdir = c.get('main', 'logdir')
logfile = c.get('main', 'logfile')

try:
    os.makedirs(logdir)
except OSError:
    if not osp.isdir(logdir):
        raise

log_path = osp.join(logdir, logfile)
log_formatter = logging.Formatter('%(asctime)s\t%(message)s',
                                  datefmt='%Y-%m-%dT%H:%M:%S%z')
log_formatter.converter = time.gmtime # HINT force logging in UTC
        # http://stackoverflow.com/a/27858760
        # https://mail.python.org/pipermail/python-dev/2010-August/102842.html
        # http://bugs.python.org/issue9527
        # http://stackoverflow.com/a/23016544
log_handler = TimedRotatingFileHandler(log_path, when='midnight')
        # HINT file rotation still occurs on LOCAL time
log_handler.setFormatter(log_formatter)
log_handler.suffix = '%Y-%m-%d.tsv'
log = logging.getLogger('typek-logger')
log.setLevel(logging.INFO)
log.addHandler(log_handler)

# HINT for testing instead of `print()`s
#log.addHandler(StreamHandler())

sensor = MAX.MAX31855(CLK, CS, DO)

while True:
    tmpr, ltmpr = sensor.readTempC(), sensor.readLinearizedTempC()
    log.info('\t'.join(['{:0.2F}'.format(tmpr),
                        '{:0.2F}'.format(ltmpr)]))
    time.sleep(interval)
