#! /usr/bin/env python
# 
# Copyright (c) 2011 SEOmoz
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

import os
import urllib2
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class PingMetric(Metric):
  def reconfig(self, url, **kwargs):
    '''parameters: url, [ post={}, timeout=30 ]'''
    Metric.reconfig(self, **kwargs)
    self.url  = url
  
  def values(self):
    start = datetime.datetime.now()
    try:
      result = urllib2.urlopen(self.url, self.post).read()
    except urllib2.HTTPError:
      pass
    except IOError:
      raise MetricException('Failed to fetch %s' % self.url)
    try:
      # Apparently different implementations don't expose this
      latency = (datetime.datetime.now() - start).total_seconds()
    except AttributeError:
      latency = (datetime.datetime.now() - start).seconds
    return {
      'results': {
      'latency': (latency, 'Seconds')
      }
    }
