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

import re
import subprocess
from sauron import logger
from sauron.metrics import Metric, MetricException

class ShellMetric(Metric):
    def __init__(self, name, cmd, units, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, cmd, units)
    
    def reconfig(self, name, cmd, units, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        self.cmd   = cmd
        self.units = units
    
    def values(self):
        try:
            res = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
            return {'results' : { self.name : (res, self.units) } }
        except ValueError:
            raise MetricException('Invalid call to Popen for %s' % cmd)
        except OSError as e:
            raise MetricException(e)

if __name__ == '__main__':
    m = ShellMetric('testing', **{'count':'ls -l | wc -l', 'count-units':'Count'})
    print repr(m.values())