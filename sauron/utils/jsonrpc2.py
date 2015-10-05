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

import json
from twisted.protocols.basic import LineReceiver
from twisted.internet import defer

class Request(object):
  def __init__(self,protocol,method):
    self.protocol = protocol
    self.method = method
  def __call__(self,*args,**kwargs):
    return self.protocol.callRemote(self.method,*args,**kwargs)
  def notify(self,*args,**kwargs):
    return self.protocol.notifyRemote(self.method,*args,**kwargs)

class Response(Exception):
  def __init__(self,value=None):
    self.value = value
  def format(self,ctx):
    return {'jsonrpc':'2.0','result':self.value,'id':ctx}

class ProtocolException(Exception):
  def __init__(self,code,message,data=None):
    self.code = int(code)
    self.message = unicode(message)
    self.data = data
  def __repr__(self):
    return 'ProtocolException(%d,%s,%s)'%(self.code,repr(self.message),repr(self.data))
  def format(self,ctx=None):
    e = {'code':self.code,'message':self.message}
    if self.data is not None:
      e['data'] = self.data
    return {'jsonrpc':'2.0','error':e,'id':ctx}
  @staticmethod
  def stringify(self,ex):
    return json.dumps({'jsonrpc':'2.0','error':{'code':-32000,'message':ex.__class__.__name__,'data':str(ex)},'id':None},separators=(',',':'))

class ParseError(ProtocolException):
  def __init__(self,message='Parse error.',data=None):
    ProtocolException.__init__(self,-32700,message,data)

class InvalidRequest(ProtocolException):
  def __init__(self,message='Invalid request.',data=None):
    ProtocolException.__init__(self,-32600,message,data)

class MethodNotFound(ProtocolException):
  def __init__(self,message='Method not found.',data=None):
    ProtocolException.__init__(self,-32601,message,data)

class InvalidParams(ProtocolException):
  def __init__(self,message='Invalid parameters.',data=None):
    ProtocolException.__init__(self,-32602,message,data)

class InternalError(ProtocolException):
  def __init__(self,message='Internal error.',data=None):
    ProtocolException.__init__(self,-32603,message,data)

class PythonError(ProtocolException):
  def __init__(self,ex):
    ProtocolException.__init__(self,-32000,ex.__class__.__name__)

class JsonRPCProtocol(LineReceiver):
  delimiter = '\n'
  def __init__(self):
    self._buf = None
    self._request = {}
    self._deferred = {}
  def lineReceived(self,line):
    try:
      try:
        data = json.loads(line)
      except ValueError:
        data = (None,)
        raise ParseError()
      res = defer.maybeDeferred(self.jsonReceived,data)
      res.addCallback(self.sendJson)
    except ProtocolException,ex:
      self.sendJson(ex.format(None))
  def jsonReceived(self,data):
    if isinstance(data,dict):
      data_id = None
      try:
        if data.get('jsonrpc',None) != '2.0':
          raise InvalidRequest()
        if 'method' in data:
          if 'id' in data:
            data_id = data['id']
            if not (isinstance(data_id,basestring) or isinstance(data_id,float) or isinstance(data_id,int) or data_id is None):
              data_id = None
              raise InvalidRequest()
          else:
            data_id = False
          data_method = data['method']
          if not isinstance(data_method,basestring):
            raise InvalidRequest()
          try:
            fn = getattr(self,'jsonrpc_'+data_method)
          except AttributeError:
            raise MethodNotFound()
          if 'params' in data:
            data_params = data['params']
            if isinstance(data_params,list):
              try:
                response = fn(*data_params)
              except Exception,ex:
                raise PythonError(ex)
            elif isinstance(data_params,dict):
             # try:
                response = fn(**data_params)
             # except Exception,ex:
            #    raise PythonError(ex)
            else:
              raise InvalidRequest()
          else:
            try:
              response = fn()
            except Exception,ex:
              raise PythonError(ex)
          if data_id is not False:
            raise Response(response)
        elif 'result' in data:
          if 'error' in data or 'id' not in data:
            raise InvalidRequest()
          data_id = data['id']
          try:
            deferred = self._deferred[data_id]
            del self._deferred[data_id]
          except KeyError:
            return
          deferred.callback(data['result'])
        elif 'error' in data:
          if 'result' in data or 'id' not in data:
            raise InvalidRequest()
          data_id = data['id']
          try:
            deferred = self._deferred[data_id]
            del self._deferred[data_id]
          except KeyError:
            return
          deferred.errback(data['error'])
      except (Response,ProtocolException),ex:
        if data_id is not False:
          return ex.format(data_id)
    elif isinstance(data,list):
      @defer.inlineCallbacks
      def runall():
        responses = []
        for request in data:
          if isinstance(request,dict):
            response = yield defer.maybeDeferred(self.jsonReceived,request)
            if response is not None:
              responses.append(response)
        defer.returnValue(responses)
      return runall()
  def sendJson(self,data):
    if isinstance(data,dict) or isinstance(data,list):
     self.sendLine(json.dumps(data,separators=(',',':')))
  def callRemote(self,_method,*args,**kwargs):
    largs = len(args)
    lkwargs = len(kwargs)
    if largs > 0 and lkwargs > 0:
      raise TypeError('cannot use both positional and named parameters')
    elif largs > 0:
      params = args
    elif lkwargs > 0:
      params = kwargs
    else:
      params = None
    d = defer.Deferred()
    try:
      ctx = max(self._deferred)+1
    except ValueError:
      ctx = 0
    o = {'jsonrpc':'2.0','method':_method,'id':ctx}
    if params is not None:
      o['params'] = params 
    self._deferred[ctx] = d
    if isinstance(self._buf,list):
      self._buf.append(o)
    else:
      self.sendJson(o)
    return d
  def notifyRemote(self,_method,*args,**kwargs):
    largs = len(args)
    lkwargs = len(kwargs)
    if largs > 0 and lkwargs > 0:
      raise TypeError('cannot use both positional and named parameters')
    elif largs > 0:
      params = args
    elif lkwargs > 0:
      params = kwargs
    else:
      params = None
    o = {'jsonrpc':'2.0','method':_method}
    if params is not None:
      o['params'] = params
    if isinstance(self._buf,list):
      self._buf.append(o)
    else:
      self.sendJson(o)
    return self
  def beginQueue(self):
    self.endQueue()
    self._buf = []
    return self
  def endQueue(self):
    if isinstance(self._buf,list):
      self.sendJson(self._buf)
    self._buf = None
    return self
  def __getattr__(self,key):
    if key.startswith('_'):
      raise AttributeError('%s instance has no attribute \'%s\''%(self.__class__.__name__,key))
    try:
      return self._request[key]
    except KeyError:
      self._request[key] = Request(self,key)
      return self._request[key]
