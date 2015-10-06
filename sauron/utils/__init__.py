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

from twisted.internet.protocol import ServerFactory, ClientFactory
import jsonrpc2
from sauron import logger
from Queue import Full

unitlist = [
      'Seconds',
      'Bytes',
      'Bits',
      'Percent',
      'Count',
      'Bytes/Second',
      'Bits/Second',
      'Count/Second'
]

class ExernalMetricProtocol(jsonrpc2.JsonRPCProtocol): 
  def jsonrpc_echo(self,*args, **kwargs):
    largs = len(args)
    if largs == 1:
      logger.debug('%s receive %s' % (str(self.factory.__class__.__name__), args[0]))
      return args[0]
    elif largs > 1:
      logger.debug('%s receive %s' % (str(self.factory.__class__.__name__), args))
      return args
  def jsonrpc_bounce(self, *args):
    self.notifyRemote('echo',*args)
    largs = len(args)
    if largs == 1:
      return args[0]
    elif largs > 1:
      return args
  def _validate_incoming(self, value, name, unit):
    logger.debug("validate external metric data")
    if not unit in unitlist:
      raise jsonrpc2.InvalidParams('Unit parameter is invalid, see AWS Cloudwatch docs')
    if not value:
      raise jsonrpc2.InvalidParams('A value parameter has to be provided')
    if not name:
      raise jsonrpc2.InvalidParams('A metricname has to be provided as \"name\" parameter')
    try:
      value = float(value)
    except ValueError:
      raise jsonrpc2.InvalidParams('Value has to be decimal')
    return value, name, unit

  def jsonrpc_put_sum_data(self, value=None, name=None, unit='Count'):
    value, name, unit = self._validate_incoming(value, name, unit)
    method = 'sum'
    self.factory.add_to_queue(name, value, unit, method)
    return "added"

  def jsonrpc_put_avg_data(self, value=None, name=None, unit='Count'):
    value, name, unit = self._validate_incoming(value, name, unit)
    method = 'avg'
    self.factory.add_to_queue(name, value, unit, method)
    return "added"

  def jsonrpc_put_persec_data(self, value=None, name=None, unit='Count'):
    value, name, unit = self._validate_incoming(value, name, unit)
    method = 'persecond'
    self.factory.add_to_queue(name, value, unit, method)
    return "added"

class ExternalListenerFactory(ServerFactory):
  protocol = ExernalMetricProtocol
  def __init__(self, queue):
    self.queue = queue
  def add_to_queue(self, *args):
    try:
      if not self.queue.full():
        logger.debug("queueing external metric data: %s, with data: %s" % (args[0], str(args[1:4])))
        self.queue.put_nowait(args)
    except Full:
      raise jsonrpc2.InternalError('metric queue is full, cannot put data into it!')
