#! /usr/bin/env python
# 
# Copyright (c) 2015 webratz
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

from datetime import datetime, time
from sauron import logger
from sauron.metrics import Metric, MetricException

class TimeMetric(Metric):
    """
    return 1 during the given timeframe. This can be used for self implementing
    scheduled autoscaling
    """
    def __init__(self, name, start, stop, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, start, stop)

    def reconfig(self, name, start, stop, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        self.start = start
        self.stop  = stop

    def values(self):
        val = 0
        try:
            now = datetime.now().time()
            start_dt = datetime.strptime(self.start, "%H:%M").time()
            stop_dt  = datetime.strptime(self.stop, "%H:%M").time()
            if now >= start_dt and now <= stop_dt:
               val = 1
            else:
               val = 0
            return {'results' : { self.name : (val, 'Count') } }
        except:
            raise

if __name__ == '__main__':
    m = TimeMetric('testing', '12:10', '20:05')
    print repr(m.values())

