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
import os
import time
import psutil
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class ProcMetric(Metric):
    def __init__(self, name, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, **kwargs)
    
    def reconfig(self, name, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        self.kwargs = kwargs
        self.kwargs['name'] = name
        re.compile(name)
        for k in ['name', 'user', 'args', 'cwd']:
            try:
                self.kwargs[k] = re.compile(self.kwargs[k])
            except KeyError:
                pass
            except re.error:
                raise MetricException('Invalid regular expression: %s' % self.kwargs[k])
        self.attrs = {
            'user-cpu'    : (ProcMetric.userCPU, 'Seconds'),
            'sys-cpu'     : (ProcMetric.sysCPU , 'Seconds'),
            'real-mem'    : (ProcMetric.realMem, 'Megabytes'),
            'virt-mem'    : (ProcMetric.virtMem, 'Megabytes'),
            'files'       : (ProcMetric.numFiles, 'Count'),
            'children'    : (ProcMetric.numChildren, 'Count'),
            'connections' : (ProcMetric.numConnections, 'Count'),
            'uptime'      : (ProcMetric.uptime, 'Seconds'),
            'percent-mem' : (psutil.Process.get_memory_percent, 'Percent'),
            'threads'     : (psutil.Process.get_num_threads, 'Count')
        }

    @staticmethod
    def userCPU(p):
        return p.get_cpu_times()[0]
    
    @staticmethod
    def sysCPU(p):
        return p.get_cpu_times()[1]
    
    @staticmethod
    def realMem(p):
        return p.get_memory_info()[0] / (1024.0 ** 2)
    
    @staticmethod
    def virtMem(p):
        return p.get_memory_info()[1] / (1024.0 ** 2)
    
    @staticmethod
    def numChildren(p):
        return len(p.get_children())
    
    @staticmethod
    def numFiles(p):
        return len(p.get_open_files())
    
    @staticmethod
    def numConnections(p):
        return len(p.get_connections())
    
    @staticmethod
    def uptime(p):
        return (time.time() - p.create_time)
    
    def match(self, p):
        try:
            for key,value in self.kwargs.items():
                if key == 'name':
                    if not value.search(p.name):
                        return False
                if key == 'user':
                    if not value.search(p.username):
                        return False
                if key == 'args':
                    if not value.search(' '.join(p.cmdline)):
                        return False
                if key == 'cwd':
                    if not value.search(p.getcwd()):
                        return False
            return True
        except psutil.error.AccessDenied:
            return False
    
    def values(self):
        try:
            results = {}
            count = 0
            for p in psutil.process_iter():
                if self.match(p):
                    count += 1
                    for key,attr in self.attrs.items():
                        r = attr[0](p)
                        try:
                            results[key][0] += r
                        except Exception:
                            results[key] = [r, attr[1]]
            results['count'] = (count, 'Count')
            return {'results': dict((k, tuple(v)) for k,v in results.items())}
        except psutil.error.AccessDenied:
            raise MetricException('Access denied for matched process.')
        except OSError as e:
            raise MetricException(e)
