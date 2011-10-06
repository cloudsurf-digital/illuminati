#! /usr/bin/env python

import os				# We need to adjust our path
import sys				# We need to append our current path
import yaml				# Read the configuration file
import time				# For sleeping
import socket			# For getting the hostname, oddly enough
import logging			# Log nicely
import datetime			# For default times

# Append our current path before this import
p = os.path.dirname(os.path.abspath(__file__))
if p not in sys.path:
	sys.path.insert(0, p)

from metrics import Metric
from emitters import Emitter

# We'll use twisted to be able to react to events,
# and to call for logging periodically
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

# Logging stuff
logger = logging.getLogger('sauron')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] @ %(module)s:%(funcName)s : %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Watcher(object):
	def __init__(self, dryrun=False):
		self.metrics   = []
		self.emitters  = []
		self.interval  = None
		self.logfile   = None
		self.dryrun    = dryrun
		self.loopingCall = None
		self.readConfig()
		
	def readConfig(self):
		data = {}
		for fname in ['/etc/sauron.yaml', 'sauron.yaml']:
			try:
				with open(fname) as f:
					f = file(fname)
					if len(data):
						print 'Warning: %s overriding prior settings' % fname
						logger.warn('%s overriding prior settings' % fname)
					data = yaml.safe_load(f)
					f.close()
			except IOError:
				pass

		self.interval = int(data.get('interval', 60))
		self.logfile  = data.get('logfile', '/var/log/sauron.log')
		# Set up the logging file
		fHandler = logging.FileHandler(self.logfile, mode='a')
		fHandler.setFormatter(formatter)
		fHandler.setLevel(logging.INFO)
		logger.addHandler(fHandler)
		
		# Read in /all/ the metrics!
		try:
			if len(data['metrics']) == 0:
				logger.error('No metrics in config file!')
				exit(1)
			for key,value in data['metrics'].items():
				try:
					module = value['module']
					m = __import__('metrics.%s' % module)
					m = getattr(m, module)
					c = getattr(m, module)
					d = dict(value.items())
					del d['module']
					d['name'] = key
					self.metrics.append(c(**d))
				except KeyError:
					logger.exception('No module listed for metric %s' % key)
					exit(1)
				except ImportError:
					logger.exception('Unable to import module %s' % module)
					exit(1)
				except TypeError as e:
					logger.exception('Unable to initialize metric %s' % key)
					exit(1)
				except Metric.MetricException as e:
					logger.exception('Module Exception %s' % module)
					exit(1)
		except KeyError:
			logger.error('No metrics in config file!')
			exit(1)
		
		# Read in /all/ the emitters!
		try:
			if self.dryrun:
				logger.warn('Skipping all emitters because of --dry-run')
				self.emitters.append(Emitter.Emitter())
				return
			if len(data['emitters']) == 0:
				logger.error('No metrics in config file!')
				exit(1)
			for key,value in data['emitters'].items():
				try:
					m = __import__('emitters.%s' % key)
					m = getattr(m, key)
					c = getattr(m, key)
					d = dict(value.items())
					self.emitters.append(c(**d))
				except ImportError:
					logger.exception('Unable to import module %s' % key)
					exit(1)
				except TypeError as e:
					logger.exception('Unable to initialize emitter %s' % key)
					exit(1)
				except Emitter.EmitterException as e:
					logger.exception('Error with module %s' % module)
					exit(1)
		except:
			logger.exception('Emitter error!')
			exit(1)
	
	def sample(self):
		logger.info('Reporting metrics...')
		results = {}
		# Aggregate all the metrics
		for m in self.metrics:
			logger.info('Querying %s' % m.name)
			# Try to get values
			try:
				results[m.name] = m.getValues()
			except Metric.MetricException as e:
				logger.exception('Error with metric.')
			except:
				logger.exception('Uncaught expection')
		# Having aggregated all the metrics, pass it through all the emitters
		for e in self.emitters:
			try:
				e.metrics(results)
			except Emitter.EmitterException:
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
		