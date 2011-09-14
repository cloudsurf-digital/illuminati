#! /usr/bin/env python

import tweepy
import Emitter
import logging

logger = logging.getLogger('sauron')

class Twitter(Emitter.Emitter):
	def __init__(self, consumer_key, consumer_secret, access_token=None, access_secret=None):
		super(Twitter,self).__init__()
		# https://github.com/tweepy/tweepy/blob/master/
		self.auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
		if not access_token or not access_secret:
			try:
				logger.warn('To authenticate, visit : %s' % self.auth.get_authorization_url())
				verifier = raw_input('Verifier: ')
			except tweepy.error.TweepError:
				raise Emitter.EmitterException('Failed to request token.')
			try:
				logger.info(repr(self.auth.get_access_token(verifier)))
			except tweepy.error.TweepError:
				raise Emitter.EmitterException('Error! Failed to get access token.')
		else:
			self.auth.set_access_token(access_token, access_secret)
		self.api = tweepy.API(self.auth)
	
	def metrics(self, metrics):
		for name, results in metrics.items():
			for key,value in results['results'].items():
				self.logger.info('Pushing %s-%s => %s' % (name, key, repr(value)))
				v, u = value
				try:
					self.api.update_status('%s-%s => %s %s' % (name, key, repr(v), u))
				except tweepy.error.TweepError as e:
					logger.error(repr(e.reason))