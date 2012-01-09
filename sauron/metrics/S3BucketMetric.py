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

import os
import datetime
from sauron import logger
from boto.exception import BotoClientError
from boto.s3.connection import S3Connection
from sauron.metrics import Metric, MetricException

class S3BucketMetric(Metric):
    def __init__(self, name, bucket, keys=None, **kwargs):
        Metric.__init__(self, name, keys, **kwargs)
        self.reconfig(name, bucket, keys, **kwargs)

    def reconfig(self, name, bucket, keys=None, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        self.bucketName = bucket
        self.prefix = kwargs.get('prefix', '')
        try:
            self.conn = S3Connection(kwargs.get('aws_id', None), kwargs.get('aws_secret', None))
            self.bucket = self.conn.get_bucket(bucket)
        except BotoClientError as e:
            raise MetricException(repr(e))
        
    def values(self):
        try:
            self.bucket = self.conn.get_bucket(self.bucketName)
            now = datetime.datetime.now()
            youngest = 100
            oldest = 0
            count = 0
            for k in self.bucket.list(self.prefix):
                mod = datetime.datetime.strptime(k.last_modified, '%Y-%m-%dT%H:%M:%S.000Z')
                age = (now - mod).seconds
                if youngest > age:
                    youngest = age
                if oldest < age:
                    oldest = age
                count += 1
            return {
                'results' : {
                    'count' : (count, 'Count'),
                    'oldest' : (oldest, 'Seconds'),
                    'youngest': (youngest, 'Seconds')
                }
            }
            
            results = []
            len()
        except BotoClientError as e:
            raise MetricException(repr(e))
        except ValueError as e:
            # Time misparsing can cause this
            raise MetricException(repr(e))
