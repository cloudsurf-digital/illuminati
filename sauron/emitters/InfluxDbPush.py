#! /usr/bin/env python
#
# Copyright (c) 2016 johnny-die-tulpe
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

import datetime, socket
from sauron import logger
from sauron.emitters import Emitter, EmitterException
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

class InfluxDbPush(Emitter):
  def __init__(self, host, port, user, password, dbname='illuminati', **kwargs):
    Emitter.__init__(self)
    self.client = InfluxDBClient(host, port, user, password, dbname)
    try:
      self.client.create_database(dbname)
    except InfluxDBClientError as e:
      logger.error(str(e))
    self.client.switch_database(dbname)
    self.tags = kwargs
    self.tags['host'] = socket.getfqdn()


  def metrics(self, metrics):
    payload = []
    for name, results in metrics.items():
      for key,value in results['results'].items():
        v, u = value
        datapoint = { "measurement": "%s-%s" % (name, key),
                      self.tags,
                      "time": int(datetime.datetime.now().strftime('%s')),
                      "fields": { "value": v }
        }
        logger.info('To InfluxDB %s-%s => %s' % (name, key, repr(value)))
        payload.append(datapoint)
    self.client.write_points(payload)
