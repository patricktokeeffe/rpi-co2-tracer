#!/usr/bin/python2
#
# Record & report data from CO2/H2O analyzer
#
# Expects LI840A connected via RS232-to-USB adapter on
# lower-right (?) USB port
#
#

from __future__ import print_function

import logging
import serial
import json
import time

from xml.etree import cElementTree as ET

import paho.mqtt.client as paho


########    CONFIG    ######################
broker_addr = '10.1.1.4'
broker_port = '1883'
report_topic = 'home/tracer/li840a/state'
report_interval = 9.6 # secs
    # HINT use less than 10 sec to prevent
    # interval stretching but more than
    # next lowest record interval (9.5sec)
############################################


from logging.handlers import TimedRotatingFileHandler 
#                              SocketHandler,
#                              DEFAULT_TCP_LOGGING_PORT)

tsvlog = logging.getLogger('li840a.raw.tsv')
tsvlog.setLevel(logging.INFO)
tsvlogfile = TimedRotatingFileHandler('/var/log/li840a/1hz/co2',
                                      when='midnight')
tsvlogfile.suffix = '%Y-%m-%d.tsv'
tsvlogfile.setFormatter(logging.Formatter('%(asctime)s\t%(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S'))
tsvlog.addHandler(tsvlogfile)
#tsvlogsocket = SocketHandler('127.0.0.1', 65478)#DEFAULT_TCP_LOGGING_PORT)
#tsvlog.addHandler(tsvlogsocket)

co2port = serial.Serial('/dev/ttyAMA0', 9600, timeout=1.0)
columns = ['co2', 'h2o', 'celltemp', 'cellpres', 'h2odewpoint', 'ivolt']
units = ['ppmv', 'ppthv', 'degC', 'kPa', 'degC', 'Vdc']
tsv_names = ['co2', 'h2o', 'T_cell', 'P_cell', 'T_dew', 'pwr_in']

#### MQTT integration
client = paho.Client()
client.connect(broker_addr, broker_port)
client.loop_start()
report = ('{{"tstamp": {ts:.2f}, "co2": {co2:.3f}, "h2o": {h2o:.3f}, '
          '"cell_T": {cell_T:.3f}, "cell_P": {cell_P:.3f}, "dewpoint": '
          '{dp:.3f}, "pwr_src": {pwr:.3f}}}')
# HINT initialize report rate limiter flag
last_report_time = time.time() - report_interval


while True:
    try:
        d = dict()

        ## HINT waits up to 1sec for new record
        xmlrec = co2port.readline()
        datatree = ET.fromstring(xmlrec)[0]
        
        for name in columns:
            d[name] = float(datatree.find(name).text)

        now = time.time()
        tsvlog.info("\t".join([str(d[x]) for x in columns]))

        if (now - last_report_time) > report_interval:
            last_report_time = now
            client.publish(report_topic,
                           report.format(ts=now,
                                         co2=d['co2'],
                                         h2o=d['h2o'],
                                         cell_T=d['celltemp'],
                                         cell_P=d['cellpres'],
                                         dp=d['h2odewpoint'],
                                         pwr=d['ivolt']),
                           qos=1, retain=True)

        #print(json.dumps(d))
        #screen.addstr(0, 0, "Cell T: {0}".format(T_cell))
        #screen.refresh()
    except ET.ParseError:
        ## ignore garbled messages (typ. for 1st msg after connect)
        continue
    except (KeyboardInterrupt, SystemExit):
        client.loop_stop()
        raise
    except:
        pass
