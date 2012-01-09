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

import os               # We need to adjust our path
import sys              # We need to append our current path
import yaml             # Read the configuration file
import time             # For sleeping
import socket           # For getting the hostname, oddly enough
import logging          # Log nicely
import datetime         # For default times

# Logging stuff
logger = logging.getLogger('sauron')
logger.setLevel(logging.INFO)

from metrics  import Metric,  MetricException
from emitters import Emitter, EmitterException

# We'll use twisted to be able to react to events,
# and to call for logging periodically
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] @ %(module)s:%(funcName)s : %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Watcher(object):
    def __init__(self, dryrun=False):
        self.metrics   = {}
        self.emitters  = {}
        self.interval  = None
        self.loghandler= None
        self.dryrun    = dryrun
        self.loopingCall = None
        self.files = {'/etc/sauron.yaml':None, 'sauron.yaml':None}
        self.readconfig()
    
    def readconfig(self):
        data = {}
        for fname, updated in self.files.items():
            try:
                # Get the last time this file was updated, if ever
                mtime = os.stat(fname).st_mtime
                if not updated or (mtime > self.files[fname]):
                    with open(fname) as f:
                        f = file(fname)
                        if data:
                            print 'Warning: %s overriding prior settings' % fname
                            logger.warn('%s overriding prior settings' % fname)
                        data = yaml.safe_load(f)
                        f.close()
                        self.files[fname] = mtime
            except IOError:
                pass
            except OSError:
                pass
            except Exception:
                logger.exception('Reconfig failure.')
        if data:
            logger.info('Reading configuration')
            self.reconfig(data)
        
    def reconfig(self, data):
        self.interval = int(data.get('interval', 60))
        if self.loghandler:
            logger.removeHandler(self.loghandler)
        fname = data.get('logfile', '/var/log/sauron.log')
        # Set up the logging file
        self.loghandler = logging.FileHandler(fname, mode='a')
        self.loghandler.setFormatter(formatter)
        self.loghandler.setLevel(logging.INFO)
        logger.addHandler(self.loghandler)
        
        # Read in /all/ the metrics!
        try:
            if len(data['metrics']) == 0:
                logger.error('No metrics in config file!')
                exit(1)
            for key,value in data['metrics'].items():
                try:
                    try:
                        d = dict(value.items())
                        self.metrics[key].reconfig(**d)
                    except:
                        module = value['module']
                        m = __import__('sauron.metrics.%s' % module)
                        m = getattr(m, 'metrics')
                        m = getattr(m, module)
                        c = getattr(m, module)
                        del d['module']
                        d['name'] = key
                        self.metrics[key] = c(**d)
                except KeyError:
                    logger.exception('No module listed for metric %s' % key)
                    exit(1)
                except ImportError:
                    logger.exception('Unable to import module %s' % module)
                    exit(1)
                except TypeError as e:
                    logger.exception('Unable to initialize metric %s' % key)
                    exit(1)
                except MetricException as e:
                    logger.exception('Module Exception %s' % module)
                    exit(1)
        except KeyError:
            logger.error('No metrics in config file!')
            exit(1)
        
        # Read in /all/ the emitters!
        try:
            if self.dryrun:
                logger.warn('Skipping all emitters because of --dry-run')
                self.emitters[''] = Emitter()
                return
            if len(data['emitters']) == 0:
                logger.error('No metrics in config file!')
                exit(1)
            for key,value in data['emitters'].items():
                try:
                    m = __import__('sauron.emitters.%s' % key)
                    m = getattr(m, 'emitters')
                    m = getattr(m, key)
                    c = getattr(m, key)
                    d = dict(value.items())
                    self.emitters[key] = c(**d)
                except ImportError:
                    logger.exception('Unable to import module %s' % key)
                    exit(1)
                except TypeError as e:
                    logger.exception('Unable to initialize emitter %s' % key)
                    exit(1)
                except EmitterException as e:
                    logger.exception('Error with module %s' % module)
                    exit(1)
        except:
            logger.exception('Emitter error!')
            exit(1)
    
    def sample(self):
        # Try to re-read the configuration files
        self.readconfig()
        logger.info('Reporting metrics...')
        results = {}
        # Aggregate all the metrics
        for m in self.metrics.values():
            logger.info('Querying %s' % m.name)
            # Try to get values
            try:
                results[m.name] = m.getValues()
            except MetricException as e:
                logger.exception('Error with metric.')
            except:
                logger.exception('Uncaught expection')
        # Having aggregated all the metrics, pass it through all the emitters
        for e in self.emitters.values():
            try:
                e.metrics(results)
            except EmitterException:
                logger.exception('Emitter exception')
            except:
                logger.exception('Uncaught expection')
        
    def start(self):
        if self.loopingCall:
            logger.warn('Watcher::run called multiple times!')
        else:
            try:
                self.loopingCall = LoopingCall(self.sample)
                self.loopingCall.start(self.interval)
                reactor.run()
            except:
                logger.exception('Error starting')
    
    def stop(self):
        logger.warn('Stopping watcher sampling!')
        try:
            self.loopingCall.stop()
            self.loopingCall = None
        except:
            logger.exception('Error stopping')
        