#!/usr/bin/python
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

from logging.handlers import TimedRotatingFileHandler 
#                              SocketHandler,
#                              DEFAULT_TCP_LOGGING_PORT)

tsvlog = logging.getLogger('li840a.raw.tsv')
tsvlog.setLevel(logging.INFO)
tsvlogfile = TimedRotatingFileHandler('/var/log/li840a/raw/tsv/co2',
                                      when='midnight')
tsvlogfile.suffix = '%Y-%m-%d.tsv'
tsvlogfile.setFormatter(logging.Formatter('%(asctime)s\t%(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S'))
tsvlog.addHandler(tsvlogfile)
#tsvlogsocket = SocketHandler('127.0.0.1', 65478)#DEFAULT_TCP_LOGGING_PORT)
#tsvlog.addHandler(tsvlogsocket)

co2port = serial.Serial('/dev/li840a', 9600, timeout=1.0)
columns = ['co2', 'h2o', 'celltemp', 'cellpres', 'h2odewpoint', 'ivolt']
units = ['ppmv', 'ppthv', 'degC', 'kPa', 'degC', 'Vdc']
tsv_names = ['co2', 'h2o', 'T_cell', 'P_cell', 'T_dew', 'pwr_in']

d = dict()
while True:
    try:
        ## waits up to 1sec for new record
        xmlrec = co2port.readline()
        ## parse XML, skip outer nodes (<li840></li840>)
        datatree = ET.fromstring(xmlrec)[0]
        
        for name in columns:
            ## lookup values, coerce to float, store in dict
            d[name] = float(datatree.find(name).text)
        ## save to tab-separated file
        tsvlog.info("\t".join([str(d[x]) for x in columns]))

        #print(json.dumps(d))
        #screen.addstr(0, 0, "Cell T: {0}".format(T_cell))
        #screen.refresh()
    except ET.ParseError:
        ## ignore garbled messages (typ. for 1st msg after connect)
        continue
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass
