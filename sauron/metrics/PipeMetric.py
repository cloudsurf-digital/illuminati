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
import select
from sauron import logger
from sauron.metrics import Metric, MetricException

class PipeMetric(Metric):
    def __init__(self, name, path, **kwargs):
        Metric.__init__(self, name)
        self.reconfig(name, path, **kwargs)
    
    def reconfig(self, path, **kwargs):
        self.patterns = dict([(k, re.compile(v)) for k,v in kwargs.items()])
        self.path = path
        try:
            os.mkfifo(self.path)
        except OSError:
            logger.warn('Path "%s" already exists. Treating like fifo...' % self.path)
        self.f    = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        self.stat = os.fstat(self.f)
    
    def __del__(self):
        try:
            os.close(self.f)
        except ValueError:
            pass
        except AttributeError:
            pass
    
    def values(self):
        # Alright, first get new stats on the file
        s = os.fstat(self.f)
        # The lines we've read
        lines = []
        # Now, see if the file was nuked
        # I'm not sure how this works. Checking inode might not really capture
        # what we're talking about. It certainly happens when the file is replaced,
        # but there /may/ be other times when it changes
        if s.st_ino != self.stat.st_ino:
            logger.warn('Inode for %s has changed' % self.path)
            os.close(self.f)
            self.f = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        elif s.st_mtime > self.stat.st_mtime:
            # If it's been modified since we last checked...
            r, w, e = select.select([self.f], [], [], 0)
            # And it's not read-ready, then we have to actually re-open it
            if len(r) == 0:
                os.close(self.f)
                self.f = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        
        # Now, remember the current stats
        self.stat = s       
        
        # Now, let's check to see if it's ready for some reading
        content = ''
        r, w, e = select.select([self.f], [], [], 0)
        while len(r):
            content += os.read(self.f, 1024)
            r, w, e = select.select([self.f], [], [], 0)
        
        # Now, split it into lines
        lines = content.strip().split('\n')
        
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
