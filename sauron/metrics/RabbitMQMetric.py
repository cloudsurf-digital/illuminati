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

from urllib import quote, urlopen
from json import load

from sauron.metrics import Metric, MetricException

class RabbitMQMetric(Metric):
    def __init__(self, name, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, **kwargs)

    def reconfig(self, name, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        rabbitmq_default = {
            'host': 'localhost',
            'port': 55672,
            'user': 'guest',
            'password': 'guest',
            'vhost': '/'}
        rabbitmq_url_parts = dict([(k, kwargs.get(k, rabbitmq_default[k])) for k in rabbitmq_default.keys()])
        rabbitmq_url_parts['vhost'] = quote(rabbitmq_url_parts['vhost'], '')
        self.queues_api_url = 'http://%(user)s:%(password)s@%(host)s:%(port)i/api/queues/%(vhost)s' % rabbitmq_url_parts
        self.queue_names = kwargs['queues']

    def values(self):
        try:
            queue_infos = load(urlopen(self.queues_api_url))
        except Exception, e:
            raise MetricException(e)

        results = {}
        for info in queue_infos:
            if info['name'] in self.queue_names:
                queue_name = info['name']
                queue_results = {
                    queue_name + '_messages_details_rate': (info['messages_details']['rate'], 'Count'),
                    queue_name + '_messages_unacknowledged_details_rate': (info['messages_unacknowledged_details']['rate'], 'Count'),
                    queue_name + '_messages_ready_details_rate': (info['messages_ready_details']['rate'], 'Count'),
                    queue_name + '_messages': (info['messages'], 'Count'),
                    queue_name + '_messages_unacknowledged': (info['messages_unacknowledged'], 'Count'),
                    queue_name + '_messages_ready': (info['messages_ready'], 'Count'),
                    queue_name + '_memory': (info['memory'] / 1000000, 'Megabytes')}

                stats_default = {
                    'publish_details': {'rate': 0},
                    'deliver_no_ack_details': {'rate': 0},
                    'deliver_get_details': {'rate': 0}}
                message_stats = info.get('message_stats', stats_default)
                for key in ('publish_details', 'deliver_no_ack_details', 'deliver_get_details'):
                    queue_results[queue_name + '_' + key + '_rate'] = (message_stats[key]['rate'], 'Count')

                results = dict(results.items() + queue_results.items())

        return {'results': results}
