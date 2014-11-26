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
    'CPULoad' : 'Count',
    'ReqPerSec' : 'Count/Second',
    'BytesPerSec': 'Bytes/Second',
    'BusyWorkers': 'Count',
    'IdleWorkers': 'Count',
    'FreeClients': 'Count'
  }
  def __init__(self, name, url, **kwargs):
    Metric.__init__(self, name, **kwargs)
    self.reconfig(name, url, **kwargs)
  
  def reconfig(self, name, url, metrics, **kwargs):
    Metric.reconfig(self, name, **kwargs)
    self.name = name
    self.url = url
    if not isinstance(metrics, list):
      raise MetricException('metrics should be a list')
    self.serverstatus_metrics = metrics
    for metric in self.serverstatus_metrics:
      try:
        assert HttpdServerStatus.AVAILABLE_METRICS_DATA.has_key(metric)
      except AssertionError:
        raise MetricException('Metric is not available, choose out of %s' % (", ".join(self.serverstatus_metrics)))
    try:
      server_status = httplib2.Http() 
    except Exception as e:
      raise MetricException(e)

  def values(self):
    try:
      server_status = httplib2.Http() 
      response, content = server_status.request(self.url, 'GET')
      result = dict([(metric, 0) for metric in self.serverstatus_metrics])
      for line in content.splitlines():
        metricname, value = line.split(':')
        if metricname == 'Scoreboard':
          metricname = 'FreeClients'
          value = str(value.count('.'))
        value = value.strip()
        if value.startswith('.'):
          value = '0' + value
        value = float(value)
        for watched_metric in self.serverstatus_metrics:
          if metricname == watched_metric:
            result[watched_metric] = (value, HttpdServerStatus.AVAILABLE_METRICS_DATA[watched_metric])
            
      return {'results' : result }
    except Exception as e:
      raise MetricException(e)
