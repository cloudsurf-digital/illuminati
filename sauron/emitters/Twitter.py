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

import tweepy
from sauron import logger
from sauron.emitters import Emitter, EmitterException

class Twitter(Emitter):
    def __init__(self, consumer_key, consumer_secret, access_token=None, access_secret=None):
        super(Twitter,self).__init__()
        # https://github.com/tweepy/tweepy/blob/master/
        self.auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
        if not access_token or not access_secret:
            try:
                logger.warn('To authenticate, visit : %s' % self.auth.get_authorization_url())
                verifier = raw_input('Verifier: ')
            except tweepy.error.TweepError:
                raise EmitterException('Failed to request token.')
            try:
                logger.info(repr(self.auth.get_access_token(verifier)))
            except tweepy.error.TweepError:
                raise EmitterException('Error! Failed to get access token.')
        else:
            self.auth.set_access_token(access_token, access_secret)
        self.api = tweepy.API(self.auth)
    
    def metrics(self, metrics):
        for name, results in metrics.items():
            for key,value in results['results'].items():
                logger.info('Pushing %s-%s => %s' % (name, key, repr(value)))
                v, u = value
                try:
                    self.api.update_status('%s-%s => %s %s' % (name, key, repr(v), u))
                except tweepy.error.TweepError as e:
                    logger.error(repr(e.reason))