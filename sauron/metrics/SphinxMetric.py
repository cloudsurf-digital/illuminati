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
import pymysql
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class SphinxMetric(Metric):
    def __init__(self, name, host='127.0.0.1', port=9306, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, host, port)
    
    def reconfig(self, name, host='127.0.0.1', port=9306, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        self.host   = host
        self.port   = port
        self.conn   = None
        self.cur    = None
    
    def __del__(self):
        try:
            self.cur.close()
            self.conn.close()
        except AttributeError:
            pass
    
    def values(self):
        try:
            self.conn = pymysql.connect(host=self.host, port=self.port)
            self.cur = self.conn.cursor()
            self.cur.execute('show status')
            r = dict(self.cur.fetchall())
            return {
                'results' : {
                    'uptime'   : (r['uptime'], 'Seconds'),
                    'queries'  : (r['queries'], 'Count'),
                    'avg_wall' : (r['avg_query_wall'], 'Seconds'),
                    'avg_cpu'  : (r['avg_query_cpu'], 'Percent'),
                    'avg_read' : (r['avg_query_readkb'], 'Kilobytes')
                }
            }
        except pymysql.err.MySQLError:
            raise MetricException('Error connecting to sphinx searchd')
        except KeyError:
            raise MetricException('Could not find all keys in searchd status')
