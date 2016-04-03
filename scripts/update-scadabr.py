#!/usr/bin/python
#
# update scadabr with latest value; use cron to run minutely
#
# Patrick O'Keeffe

import urllib2
import subprocess
from datetime import datetime

reporturl = 'http://10.1.1.3/ScadaBR/httpds?'
deviceid = '__device=tracer'
#timestamp = datetime.now().strftime('__time=%Y%m%d%H%M00')

datafile = '/var/log/li840a/1hz/co2'
last_record = subprocess.check_output(['tail', '-n', '1', datafile]).strip()
(ts, co2, h2o, cell_T, cell_P, dew_T, pwr_src) = last_record.split('\t')

timestamp = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').strftime('__time=%Y%m%d%H%M00')

vals = ['li840a_co2=%s' % co2, 'li840a_h2o=%s' % h2o, 'li840a_cell_t=%s' % cell_T,
        'li840a_cell_p=%s' % cell_P, 'li840a_dew_t=%s' % dew_T,
        'li840a_pwr_src=%s' % pwr_src]

urllib2.urlopen(reporturl + '&'.join([deviceid, timestamp]+vals))


