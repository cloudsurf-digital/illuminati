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

import urllib2          # Need this to determine our instance ID
import datetime
from sauron import logger
from boto.sns import SNSConnection
from boto.ec2.cloudwatch.alarm import MetricAlarm
from boto.ec2.cloudwatch import CloudWatchConnection
from sauron.emitters import Emitter, EmitterException
from boto.ec2.cloudwatch.listelement import ListElement

class CloudWatch(Emitter):
    def __init__(self, namespace, dimensions={}, alarms={}, actions={}, **kwargs):
        Emitter.__init__(self)
        self.namespace = namespace
        self.conn = CloudWatchConnection(**kwargs)
        # Set our dimensions, including instance ID
        self.dims = dimensions or {}
        self.setInstanceId()
        # Make sure our actions exist...
        self.actions = {}
        # Store our AWS credential args for later
        self.kwargs = kwargs
        self.updateActions(actions)
        # Now update our alarms
        self.updateAlarms(alarms)

    def updateActions(self, actions):
        '''Update the actions on this account based on the supplied actions. Actions
        should a dictionary of Amazon Simple Notification Service topic names, and
        their associated subscriptions.'''
        # First, we need a SNS Connection to make this changes
        conn = SNSConnection(**self.kwargs)
        # Now make sure each subscription is registered to the topic
        for name, subscriptions in actions.items():
            logger.info('Creating topic %s' % name)
            # Try to make a topic
            try:
                arn = conn.create_topic(name)['CreateTopicResponse']['CreateTopicResult']['TopicArn']
                self.actions[name] = arn
            except KeyError:
                raise EmitterException('Bad response creating topic %s' % name)
            
            if len(subscriptions) == 0:
                raise EmitterException('No subscriptions for action %s' % name)
            # Now try to arrange for subscriptions
            # Oddly enough, calling create_topic doesn't have any effect
            # if the topic already exists, but calling subscribe() for an
            # existing subscription causes a second subscription to be added
            # So, we have to get a list of current subscriptions, and then
            # make sure to only add the subscription if it's currently there
            logger.info('Getting a list of current subscriptions...')
            current = conn.get_all_subscriptions_by_topic(arn)
            current = current['ListSubscriptionsByTopicResponse']
            current = current['ListSubscriptionsByTopicResult']
            current = current['Subscriptions']
            current = set(s['Endpoint'] for s in current)
            # For all desired subscriptions not present, subscribe
            for s in subscriptions:
                if s['endpoint'] not in current:
                    logger.info('Adding %s to action %s' % (s['endpoint'], name))
                    conn.subscribe(arn, s.get('protocol', 'email'), s['endpoint'])
                else:
                    logger.info('%s already subscribed to action' % s['endpoint'])
            # Check for subscriptions that are active, but not listed...
            activeUnlisted = set(current) - set([s['endpoint'] for s in subscriptions])
            for s in activeUnlisted:
                logger.warn('Subscript "%s" active, but not listed in config' % s)
    
    def updateAlarms(self, alarms):
        # Set up our alarms...
        for name, atts in alarms.items():
            # We don't pass in the alarm_actions attributes into the constructor
            try:
                alarm_actions = [self.actions[a] for a in atts.pop('alarm', [])]
                insufficient_data_actions = [self.actions[a] for a in atts.pop('insufficient_data', [])]
                ok_actions = [self.actions[a] for a in atts.pop('ok', [])]
            except KeyError as e:
                raise EmitterException('Unknown action %s' % repr(e))
            # Set some defaults:
            atts['statistic'] = atts.get('statistic', 'Average')
            atts['period'] = atts.get('period', 60)
            atts['evaluation_periods'] = atts.get('evaluation_periods', 1)
            # For each of the dimensions...
            try:
                atts['dimensions']['InstanceId'] = self.dims['InstanceId']
                atts['namespace'] = self.namespace
            except KeyError:
                pass
            a = MetricAlarm(name=name, **atts)
            a.alarm_actions = alarm_actions
            a.insufficient_data_actions = ListElement(insufficient_data_actions)
            a.ok_actions = ListElement(ok_actions)
            self.conn.update_alarm(a)
    
    # Try to find the instance ID
    def setInstanceId(self):
        try:
            # This looks a little weird, but the idea is that if you would 
            # to have the InstanceId automatically filled in, then simply
            # add the key in the yaml file, but not the value. If you'd like
            # to override it, then you can override it by providing a value.
            # So, this covers the case that the key is provided, but no value
            if self.dims and not self.dims.get('InstanceId', True):
                self.dims['InstanceId'] = urllib2.urlopen('http://169.254.169.254/1.0/meta-data/instance-id', timeout=1.0).read().strip()
        except urllib2.URLError:
            logger.warn('Failed to get an instance ID for this node from Amazon')
    
    def metrics(self, metrics):
        for name, results in metrics.items():
            for key,value in results['results'].items():
                logger.info('Pushing %s-%s => %s' % (name, key, repr(value)))
                v, u = value
                self.conn.put_metric_data(self.namespace, name + '-' + key, unit=u, value=v, dimensions=self.dims)
    
