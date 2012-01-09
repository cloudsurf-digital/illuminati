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

import httplib2
import simplejson as json
from sauron import logger
from sauron.emitters import Emitter, EmitterException

class HTTPEndpoint(Emitter):
    def __init__(self, url, method='PUT'):
        super(HTTPEndpoint,self).__init__()
        self.url = url
        self.method = method
    
    def metrics(self, metrics):
        d = {}
        for name, results in metrics.items():
            for key,value in results['results'].items():
                d[name + '-' + key] = value
        try:
            response, content = httplib2.Request(self.url, method=self.method, body=json.dumps(d))
            if response != 200:
                logger.error('%s responded with (%i) %s' % (self.url, response, content))
        except httplib2.HttpLib2Error as e:
            logger.error(repr(e))

    
