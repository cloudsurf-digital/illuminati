#! /usr/bin/env python
# 
# Copyright (c) 2015 johnny-die-tulpe
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


class NginxServerStatusMetric(Metric):
  AVAILABLE_METRICS_DATA = {
    'ActiveCon'        : 'Count',
    'CurrentReqPerSec' : 'Count/Second',
    'TotalAcceptedConn': 'Count',
    'TotalHandledConn' : 'Count',
    'TotalHandledReq'  : 'Count',
    'ClientRead'       : 'Count',
    'ClientWrite'      : 'Count',
    'IdleKeepalive'    : 'Count'
  }
  def reconfig(self, *args, **kwargs):
    Metric.reconfig(self, *args, **kwargs)
    if not isinstance(self.metrics, list):
      raise MetricException('metrics should be a list')
    self.serverstatus_metrics = self.metrics
    for metric in self.serverstatus_metrics:
      try:
        assert NginxServerStatusMetric.AVAILABLE_METRICS_DATA.has_key(metric)
      except AssertionError:
        raise MetricException('Metric is not available, choose out of %s' % (", ".join(NginxServerStatusMetric.AVAILABLE_METRICS_DATA.keys())))
    try:
      server_status = httplib2.Http() 
    except Exception as e:
      raise MetricException(e)

  def calculate_req_per_second(self, total_access):
    # only send results if req greater than 30 
    if total_access > 30 and self.serializer.has_key('last_total_access') and total_access > self.serializer['last_total_access']:
      result = abs(total_access - self.serializer['last_total_access']) / self.interval
    else:
      logger.info('requests from webserver not enough (< 100 requests) or first run, we dont send any data!')
      result = None
    self.serializer['last_total_access'] = total_access
    return result

  def get_server_status(self, url):
    http = httplib2.Http() 
    resp, content = http.request(self.url, 'GET')
    res = {}
    assert resp.status == 200 
    res['ActiveCon'] = int(content.splitlines()[0].split(': ')[1].strip())
    res['TotalAcceptedConn'], res['TotalHandledConn'], res['TotalHandledReq'] = [ int(i) for i in \
        content.splitlines()[2].split(' ') if re.match(r'\d+', i.strip()) ]
    res['ClientRead'], res['ClientWrite'], res['IdleKeepalive'] = [ int(i) for i in \
        content.splitlines()[3].split(' ') if re.match(r'\d+', i.strip()) ]
    return res 

  def values(self):
    try:
      server_status = self.get_server_status(self.url)
      server_status['CurrentReqPerSec'] = self.calculate_req_per_second(float(server_status['TotalHandledReq']))
      res_keys = set(self.serverstatus_metrics).intersection(server_status.keys())
      res = {}
      for k in res_keys:
        if server_status[k]:
          res[k] = (server_status[k], NginxServerStatusMetric.AVAILABLE_METRICS_DATA[k])
      return {'results' : res }
    except Exception as e:
      raise MetricException(e)
