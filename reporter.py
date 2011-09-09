#! /usr/bin/env python

import time				# For sleeping
import socket			# For getting the hostname, oddly enough
import urllib2			# Need this to determine our instance ID
import logging			# Log nicely
import datetime			# For default times
import ConfigParser		# For reading default configurations
from boto.ec2.cloudwatch import CloudWatchConnection
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
		self.conn      = CloudWatchConnection()
		self.metrics   = []
		self.interval  = None
		self.logfile   = None
		self.meta      = {}
		self.readConfig()
		# Try to find the instance ID
		try:
			self.meta['InstanceId'] = urllib2.urlopen('http://169.254.169.254/1.0/meta-data/instance-id', timeout=1.0).read().strip()
		except urllib2.URLError:
			logger.warn('Failed to get an instance ID for this node from Amazon')
	
	def readConfig(self):
		self.config    = ConfigParser.ConfigParser()
		# Try to read from each of these in order
		self.config.read(['sauron.conf', '/etc/sauron.conf'])
		try:
			d = dict(self.config.items('sauron'))
		except ConfigParser.NoSectionError:
			print 'No sauron section in configuration file.'
			logger.error('No sauron section in configuration file.')
			exit(1)
		for section in self.config.sections():
			if section == 'sauron':
				d = dict(self.config.items(section))
				# Now, try to set the logfile
				try:
					self.logfile = d['logfile']
					fHandler = logging.FileHandler(self.logfile, mode='a')
					fHandler.setFormatter(formatter)
					fHandler.setLevel(logging.INFO)
					logger.addHandler(fHandler)
				except KeyError:
					logger.warn('No logfile found. Not logging to file')
				
				# Try to set the interval
				try:
					self.interval = int(d['interval'])
				except KeyError:
					self.interval = 500
					logger.warn('No interval found for sauron. Using 500s')
				
				# Now try to set the namespace
				try:
					self.namespace = d['namespace']
				except KeyError:
					self.hostname = socket.gethostname()
					logger.warn('No namespace provided. Using hostname, %s' % self.hostname)				
			else:
				try:
					module, name = section.split(':')
				except ValueError:
					logger.error('Section names must be <metric>:<name>, found "%s"' % section)
					exit(3)
				m = __import__('metrics.%s' % module)
				c = getattr(m, module)
				c = getattr(c, module)
				d = dict(self.config.items(section))
				try:
					d['keys'] = [key.strip() for key in d['keys'].split(',')]
				except KeyError:
					pass
				d['name'] = name
				obj = c(**d)
				self.metrics.append(obj)
	
	def push(self, metric):
		self.metrics.append(metric)
	
	def run(self):
		while True:
			next = time.time() + self.interval
			logger.info('Reporting metrics...')
			for m in self.metrics:
				logger.info('Querying %s' % m.name)
				# Try to get values
				try:
					results = m.values()
					try:
						# The default time is now
						try:
							t = results['time']
						except KeyError:
							t = datetime.datetime.now()
							logger.debug('No time provided by metric. Using now.')
						# Go through all the results
						for key,value in results['results'].items():
							logger.info('Pushing %s-%s => %s' % (m.name, key, repr(value)))
							v, u = value
							self.conn.put_metric_data(self.namespace, m.name + '-' + key, timestamp=t, unit=u, value=v, dimensions=self.meta)
					except KeyError as e:
						logger.error('Key Error : %s' % repr(e))
				except Metric.MetricException as e:
					logger.error(repr(e))
			# Sleep until we should next run it
			time.sleep(next - time.time())

if __name__ == '__main__':
	w = Watcher()
	w.run()