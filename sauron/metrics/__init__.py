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
import sys
from sauron import logger

# Append our current path before this import
p = os.path.dirname(os.path.abspath(__file__))
if p not in sys.path:
    sys.path.insert(0, p)

class MetricException(Exception):
    def __init__(self, message):
        self.msg = message
    def __repr__(self):
        return repr(self.msg)
    def __str__(self):
        return str(self.msg)

class Metric(object):
    def __init__(self, name, serializer, keys=[], **kwargs):
        Metric.reconfig(self, name, serializer, keys)
    
    def reconfig(self, name, serializer, keys=[], **kwargs):
        self.name = name
        self.serializer = serializer
        self.keys = keys
    
    def getValues(self):
        if self.keys:
            results = self.values()
            pruned = {}
            for k in self.keys:
                try:
                    pruned[k] = results['results'][k]
                except KeyError:
                    logger.warn('Key %s unavailable' % k)
            results['results'] = pruned
            return results
        else:
            return self.values()
    
    def values(self):
        return {
            'results': {
                'key': (0, 'Count')
            }, 'time': datetime.datetime.now()
        }

class ExternalMetricQueueConsumer(Metric):
  def __init__(self, name, serializer, queue, **kwargs):
    Metric.__init__(self, name, serializer, **kwargs)
    self.reconfig(name, serializer, queue, **kwargs)

  def reconfig(self, name, serializer, queue, **kwargs):
    Metric.reconfig(self, name, serializer, **kwargs)
    self.queue = queue

  def values(self):
    try:
      res = {}
      while not self.queue.empty():
        name, value, unit = self.queue.get(True, 1)
        if res.has_key(name):
          res[name][0] += value
        else:
          res[name] = [value, unit]
        self.queue.task_done()

      for k,v in res.iteritems():
        res[k] = tuple(v)
      if not res:
        logger.info('No data from external metric listener received')
      return {'results': res}
    except Exception as e:
      raise MetricException(e)
