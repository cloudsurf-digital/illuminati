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

class ExernalMetricProtocol(jsonrpc2.JsonRPCProtocol): 
  def jsonrpc_echo(self,*args, **kwargs):
    largs = len(args)
    logger.info(str(args))
    if largs == 1:
      print self.factory.__class__.__name__,'receive:',args[0]
      return args[0]
    elif largs > 1:
      print self.factory.__class__.__name__,'receive:',args
      return args
  def jsonrpc_bounce(self,*args):
    print self.factory.__class__.__name__,'bounce'
    self.notifyRemote('echo',*args)
    largs = len(args)
    if largs == 1:
      return args[0]
    elif largs > 1:
      return args
  def jsonrpc_add(self, value=None, name=None, unit='Count'):
    logger.info("Received external metric: %s, with data: %s" % (str(name), str(value)))
    return "ok"

class ExternalListenerFactory(ServerFactory):
  protocol = ExernalMetricProtocol
