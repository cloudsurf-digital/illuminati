#! /usr/bin/env python

import yaml				# Read the configuration file
import time				# For sleeping
import socket			# For getting the hostname, oddly enough
import logging			# Log nicely
import datetime			# For default times
from metrics import Metric

# Logging stuff
logger = logging.getLogger('sauron')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] @ %(module)s:%(funcName)s : %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Watcher(object):
	def __init__(self):
		self.metrics   = []
		self.emitters  = []
		self.interval  = None
		self.logfile   = None
		self.readConfig()
	
	def error(self, message):
		print(message)
		logger.error(message)
		exit(1)
	
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
				self.error('No metrics in config file!')
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
					self.error('No module listed for metric %s' % key)
				except ImportError:
					self.error('Unable to import module %s' % module)
				except TypeError:
					self.error('Unable to initialize metric %s' % key)
				except Metric.MetricException as e:
					self.error('%s: %s' % (module, repr(e)))
		except KeyError:
			self.error('No metrics in config file!')
		
		# Read in /all/ the emitters!
		try:
			if len(data['emitters']) == 0:
				self.error('No metrics in config file!')
			for key,value in data['emitters'].items():
				try:
					m = __import__('emitters.%s' % key)
					m = getattr(m, key)
					c = getattr(m, key)
					d = dict(value.items())
					self.emitters.append(c(**d))
				except ImportError:
					self.error('Unable to import module %s' % key)
				except TypeError:
					self.error('Unable to initialize emitter %s' % key)
		except KeyError:
			self.error('No emitters in config file!')
		
	def run(self):
		while True:
			next = time.time() + self.interval
			logger.info('Reporting metrics...')
			results = {}
			# Aggregate all the metrics
			for m in self.metrics:
				logger.info('Querying %s' % m.name)
				# Try to get values
				try:
					results[m.name] = m.values()
				except Metric.MetricException as e:
					logger.error(repr(e))
			# Having aggregated all the metrics, pass it through all the emitters
			for e in self.emitters:
				e.metrics(results)
			# Sleep until we should next run it
			time.sleep(next - time.time())

if __name__ == '__main__':
	w = Watcher()
	w.run()