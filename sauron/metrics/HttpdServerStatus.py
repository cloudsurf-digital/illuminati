#! /usr/bin/env python
# 
# Copyright (c) 2014 johnny-die-tulpe
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re
import os
import httplib2
from sauron import logger
from sauron.metrics import Metric, MetricException

class HttpdServerStatus(Metric):
  AVAILABLE_METRICS_DATA = {
    'CPULoad'          : 'Count',
    'AvgReqPerSec'     : 'Count/Second',
    'CurrentReqPerSec' : 'Count/Second',
    'BytesPerSec'      : 'Bytes/Second',
    'BusyWorkers'      : 'Count',
    'IdleWorkers'      : 'Count',
    'FreeClients'      : 'Count'
  }
  def __init__(self, name, serializer, url, **kwargs):
    Metric.__init__(self, name, serializer, **kwargs)
    self.reconfig(name, serializer, url, **kwargs)
  
  def reconfig(self, name, serializer, url, metrics, interval='60', **kwargs):
    Metric.reconfig(self, name, serializer, **kwargs)
    self.url = url
    self.interval = interval
    if not isinstance(metrics, list):
      raise MetricException('metrics should be a list')
    self.serverstatus_metrics = metrics
    for metric in self.serverstatus_metrics:
      try:
        assert HttpdServerStatus.AVAILABLE_METRICS_DATA.has_key(metric)
      except AssertionError:
        raise MetricException('Metric is not available, choose out of %s' % (", ".join(HttpdServerStatus.AVAILABLE_METRICS_DATA.keys())))
    try:
      server_status = httplib2.Http() 
    except Exception as e:
      raise MetricException(e)


  def count_freeclients(self, value):
     return str(value.count('.'))

  def get_values_of_serverstatus(self, serverstatus_key, value):
    value = value.strip()
    serverstatus_key = serverstatus_key.strip()
    metricmap = {'Scoreboard'     : 'FreeClients',
                 'ReqPerSec'      : 'AvgReqPerSec',
                 'Total Accesses' : 'CurrentReqPerSec'}
    valuemap  = {'Scoreboard'     : self.count_freeclients,
                 'Total Accesses' : self.calculate_req_per_second}
    metric_mapper = lambda x: metricmap[x] if metricmap.has_key(x) else x
    metricname = metric_mapper(serverstatus_key)
    if not metricname in self.serverstatus_metrics: return None, None
    value_mapper = lambda x,y: valuemap[x](y) if valuemap.has_key(x) else y
    value = value_mapper(serverstatus_key, value)
    if value:
      if str(value).startswith('.'):
        value = '0' + value
      value = "%.3f" % (float(value))
    return metricname, value

  def calculate_req_per_second(self, total_httpd_access):
    current_access = float(total_httpd_access)
    # only send results if uptime greater than 70 seconds
    if int(self.serverstatus_result['Uptime']) > 70:
      if self.serializer.has_key('last_httpd_total_access') and current_access > self.serializer['last_httpd_total_access']:
        result = abs(current_access - self.serializer['last_httpd_total_access']) / self.interval
      else:
        # fallback to aggregated req per sec if no last_httpd_total_access value is available
        logger.info('no last state of total accesses or it\'s greater than current, falling back to apaches requests per seconds')
        result = self.serverstatus_result['ReqPerSec']
    else:
      logger.info('uptime from webserver not enough (>70 seconds), still in warump phase, we dont send any data!')
      result = None

    self.serializer['last_httpd_total_access'] = current_access
    return result

  def values(self):
    try:
      server_status = httplib2.Http() 
      response, content = server_status.request(self.url, 'GET')
      result = {}
      self.serverstatus_result = dict([line.split(': ') for line in content.splitlines() if ': ' in line])
      for k,v in self.serverstatus_result.iteritems():
        metricname, value = self.get_values_of_serverstatus(k,v)
        if value:
          result[metricname] = (value, HttpdServerStatus.AVAILABLE_METRICS_DATA[metricname])
      return {'results' : result }
    except Exception as e:
      raise MetricException(e)
