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

class MySQLMetric(Metric):
    def __init__(self, name, host=None, user=None, passwd=None, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, host, user, passwd)
    
    def reconfig(self, name, host=None, user=None, passwd=None, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        self.name   = name
        self.host   = host
        self.user   = user
        self.passwd = passwd
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
            self.conn = pymysql.connect(host=self.host, user=self.user, passwd=self.passwd)
            self.cur = self.conn.cursor()
            self.cur.execute('show status')
            r = dict(self.cur.fetchall())
            return {
                'results' : {
                    'uptime' : (r['Uptime'] , 'Seconds'),
                    'queries': (r['Queries'], 'Count')
                }
            }
        except pymysql.err.MySQLError:
            raise MetricException('Failed to connect to mySQL.')
        except KeyError:
            raise MetricException('Could not find all keys in mySQL status')
    