#! /usr/bin/env python

import Emitter
import urllib2			# Need this to determine our instance ID
import logging
import datetime
from boto.sns import SNSConnection
from boto.ec2.cloudwatch import CloudWatchConnection
from boto.ec2.cloudwatch.alarm import MetricAlarm

logger = logging.getLogger('sauron')

class CloudWatch(Emitter.Emitter):
	def __init__(self, namespace, dimensions={}, alarms={}, actions={}):
		super(CloudWatch,self).__init__()
		self.namespace = namespace
		self.conn = CloudWatchConnection()
		# Set our dimensions, including instance ID
		self.dims = dimensions
		self.setInstanceId()
		# Make sure our actions exist...
		self.actions = {}
		snsConn = SNSConnection()
		for action,atts in actions.items():
			logger.info('Creating topic %s' % action)
			# Try to make a topic
			response = snsConn.create_topic(action)
			try:
				arn = response['CreateTopicResponse']['CreateTopicResult']['TopicArn']
				self.actions[action] = arn
			except KeyError:
				raise Emitter.EmitterException('Bad response creating topic %s' % action)
			# Now try to arrange for subscriptions
			try:
				logger.info('Getting a list of current subscriptions...')
				# First, get all the subscriptions currently held
				current = snsConn.get_all_subscriptions_by_topic(arn)
				current = current['ListSubscriptionsByTopicResponse']
				current = current['ListSubscriptionsByTopicResult']
				current = current['Subscriptions']
				current = [s['Endpoint'] for s in current]
				# For all desired subscriptions not present, subscribe
				for s in atts['subscriptions']:
					if s['endpoint'] not in current:
						logger.info('Adding %s to action %s' % (s['endpoint'], action))
						snsConn.subscribe(arn, s['protocol'], s['endpoint'])
					else:
						logger.info('%s already subscribed to action' % s['endpoint'])
			except KeyError:
				raise Emitter.EmitterException('No subscriptions for action %s' % action)
		# Set up our alarms...
		for alarm,atts in alarms.items():
			alarm_actions = atts['alarm_actions']
			del atts['alarm_actions']
			# For each of the dimensions...
			try:
				atts['dimensions']['InstanceId'] = self.dims['InstanceId']
				atts['namespace'] = self.namespace
			except KeyError:
				pass
			a = MetricAlarm(name=alarm, **atts)
			try:
				for action in alarm_actions:
					a.add_alarm_action(self.actions[action])
			except KeyError:
				raise Emitter.EmitterException('Unknown action %s' % action)
			self.conn.update_alarm(a)
	
	# Try to find the instance ID
	def setInstanceId(self):
		try:
			self.dims['InstanceId'] = urllib2.urlopen('http://169.254.169.254/1.0/meta-data/instance-id', timeout=1.0).read().strip()
		except urllib2.URLError:
			self.logger.warn('Failed to get an instance ID for this node from Amazon')
	
	def metrics(self, metrics):
		t = datetime.datetime.now()
		for name, results in metrics.items():
			for key,value in results['results'].items():
				self.logger.info('Pushing %s-%s => %s' % (name, key, repr(value)))
				v, u = value
				self.conn.put_metric_data(self.namespace, name + '-' + key, timestamp=t, unit=u, value=v, dimensions=self.dims)
	
