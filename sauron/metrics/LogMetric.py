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
from sauron import logger
from sauron.metrics import Metric, MetricException

class LogMetric(Metric):
    def __init__(self, name, path, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, path, **kwargs)
    
    def reconfig(self, name, path, **kwargs):
        Metric.reconfig(self, **kwargs)
        self.name = name
        self.patterns = dict([(k, re.compile(v)) for k,v in kwargs.items()])
        self.path = path
        try:
            self.f = file(self.path)    # The file object we'll read from
        except IOError as e:
            raise MetricException(e)
        self.stat = os.lstat(self.path) # The stats on that particular file
    
    def __del__(self):
        try:
            self.f.close()
        except ValueError:
            pass
        except AttributeError:
            pass
    
    def values(self):
        try:
            # Alright, first get new stats on the file
            s = os.lstat(self.path)
            # The lines we've read
            lines = []
            # Now, see if the file was nuked
            # I'm not sure how this works. Checking inode might not really capture
            # what we're talking about. It certainly happens when the file is replaced,
            # but there /may/ be other times when it changes
            if s.st_ino != self.stat.st_ino:
                logger.warn('Inode for %s has changed' % self.path)
                self.f.close()
                self.f = file(self.path)
                lines = self.f.read(s.st_size).strip().split('\n')
            elif s.st_size < self.stat.st_size:
                logger.warn('File %s has shrunk since last read! Reading from beginning...' % self.path)
                self.f.seek(0)
                lines = self.f.read(s.st_size).strip().split('\n')
            elif s.st_mtime > self.stat.st_mtime:
                # If the file has been changed since last we looked
                self.f.seek(self.stat.st_size)
                lines = self.f.read(s.st_size - self.stat.st_size).strip().split('\n')
            # Now, remember the current stats
            self.stat = s
        
            # Now that we have all our lines, go ahead and try to match the regex to each line
            counts = dict([(k, 0) for k in self.patterns])
            for line in lines:
                for k, r in self.patterns.items():
                    m = r.search(line)
                    if m:
                        try:
                            # Use the last matching group if found
                            counts[k] += int(m.groups()[-1])
                        except ValueError:
                            logger.warn('Could not parse int from %s. Using 1' % m.gorups()[-1])
                            counts[k] += 1
                        except IndexError:
                            logger.info('No groups in regular expression. Using 1')
                            counts[k] += 1
            return {
                'results' : dict([(k, (v, 'Count')) for k, v in counts.items()])
            }
        except Exception as e:
            raise MetricException(e)
