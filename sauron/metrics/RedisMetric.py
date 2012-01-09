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

import redis
from sauron import logger
from sauron.metrics import Metric, MetricException

class RedisMetric(Metric):
    @staticmethod
    def parseMemory(x):
        try:
            if 'G' in x:
                return (x.replace('G', ''), 'Gigabytes')
            elif 'M' in x:
                return (x.replace('M', ''), 'Megabytes')
            elif 'K' in x:
                return (x.replace('K', ''), 'Kilobytes')
            else:
                return (x, 'Bytes')
        except:
            return (x, 'Bytes')
    
    infoUnits = {
        'redis_version'             : lambda x: (int(x.replace('.', '')), 'None'),
        'redis_git_sha1'            : lambda x: (int(x, 16), 'None'),
        'redis_dig_dirty'           : lambda x: (x, 'None'),
        'arch_bits'                 : lambda x: (x, 'Count'),
        'process_id'                : lambda x: (x, 'None'),
        'uptime_in_seconds'         : lambda x: (x, 'Seconds'),
        'uptime_in_days'            : lambda x: (x, 'None'),
        'lru_clock'                 : lambda x: (x, 'Seconds'),
        'used_cpu_sys'              : lambda x: (x, 'Seconds'),
        'used_cpu_user'             : lambda x: (x, 'Seconds'),
        'used_cpu_sys_children'     : lambda x: (x, 'Seconds'),
        'used_cpu_user_children'    : lambda x: (x, 'Seconds'),
        'connected_clients'         : lambda x: (x, 'Count'),
        'connected_slaves'          : lambda x: (x, 'Count'),
        'client_longest_output_list': lambda x: (x, 'Count'),
        'client_biggest_input_buf'  : lambda x: (x, 'Bytes'),
        'blocked_clients'           : lambda x: (x, 'Count'),
        'used_memory'               : lambda x: RedisMetric.parseMemory(x),
        'used_memory_human'         : lambda x: RedisMetric.parseMemory(x),
        'used_memory_rss'           : lambda x: RedisMetric.parseMemory(x),
        'used_memroy_peak'          : lambda x: RedisMetric.parseMemory(x),
        'used_memory_peak_human'    : lambda x: RedisMetric.parseMemory(x),
        'mem_fragmentation_ratio'   : lambda x: (x, 'None'),
        'loading'                   : lambda x: (x, 'None'),
        'aof_enabled'               : lambda x: (x, 'None'),
        'changes_since_last_save'   : lambda x: (x, 'Count'),
        'bgsave_in_progress'        : lambda x: (x, 'None'),
        'last_save_time'            : lambda x: (x, 'Seconds'),
        'bgrewriteaof_in_progress'  : lambda x: (x, 'None'),
        'total_connections_received': lambda x: (x, 'Count'),
        'total_commands_processed'  : lambda x: (x, 'Count'),
        'expired_keys'              : lambda x: (x, 'Count'),
        'evicted_keys'              : lambda x: (x, 'Count'),
        'keyspace_hits'             : lambda x: (x, 'Count'),
        'keyspace_misses'           : lambda x: (x, 'Count'),
        'pubsub_channels'           : lambda x: (x, 'Count'),
        'pubsub_patterns'           : lambda x: (x, 'Count'),
        'latest_fork_usec'          : lambda x: (x, 'Microseconds'),
        'vm_enabled'                : lambda x: (x, 'None'),
        'aof_current_size'          : lambda x: (x, 'Bytes'),
        'aof_base_size'             : lambda x: (x, 'Bytes'),
        'aof_pending_rewrite'       : lambda x: (x, 'None'),
    }

    def __init__(self, name, **kwargs):
        Metric.__init__(self, name, **kwargs)
        self.reconfig(name, **kwargs)
    
    def reconfig(self, name, **kwargs):
        Metric.reconfig(self, name, **kwargs)
        # These are a selection of argument names. If they're
        # present, then we'll use them, otherwise, we'll use 
        # the default provided by the redis module itself
        redisArgs = {}
        for arg in ['host', 'port', 'db', 'password', 'charset', 'errors', 'unix_socket_path']:
            try:
                redisArgs[arg] = kwargs[arg]
            except KeyError:
                pass
        self.redis  = redis.Redis(**redisArgs)
        # The keys we should save from the 'info' command in redis
        self.info   = kwargs.get('info'  , [])
        # The keys we should get and interpret as numbers
        self.get    = kwargs.get('get'   , [])
        # The keys we should get, and report their length
        self.llen   = kwargs.get('llen', [])
        # The keys we should get and report the hash length
        self.hlen   = kwargs.get('hlen', [])
        # The keys we should get and report the particular key from
        self.hget   = kwargs.get('hget', {})
        # The keys we should get and report the cardinality of
        self.scard  = kwargs.get('scard', [])
        # The keys we should get and report the zcardinality of
        self.zcard  = kwargs.get('zcard', [])
        # The patterns we should count the number of keys of
        self.patterns = kwargs.get('patterns', [])
    
    def values(self):
        try:
            results = {}
            info = self.redis.info()
            for i in self.info:
                try:
                    results[i] = RedisMetric.infoUnits[i](info[i])
                except Exception as e:
                    print repr(e)
                    results[i] = (info[i], 'None')
            
            both = list(self.get)
            both.extend(self.llen)
            both.extend(self.hlen)
            both.extend(['%s-%s' % (k, v) for k,v in self.hget.items()])
            both.extend(self.scard)
            both.extend(self.zcard)
            both.extend(self.patterns)
            with self.redis.pipeline() as pipe:
                for g in self.get:
                    logger.debug('get %s') % g
                    pipe.get(g)
                for l in self.llen:
                    logger.debug('llen %s' % l)
                    pipe.llen(l)
                for h in self.hlen:
                    logger.debug('hlen %s' % h)
                    pipe.hlen(h)
                for k,v in self.hget.items():
                    logger.debug('hget %s %s' % (k, v))
                    pipe.hget(k, v)
                for s in self.scard:
                    logger.debug('scard %s' % s)
                    pipe.scard(s)
                for z in self.zcard:
                    logger.debug('zcard %s' % z)
                    pipe.zcard(z)
                for pattern in self.patterns:
                    logger.debug('keys %s' % pattern)
                    pipe.keys(pattern)
                fetched = pipe.execute()
                for k, f in zip(both, fetched):
                    if isinstance(f, list):
                        results[k] = (len(f), 'Count')
                    else:
                        results[k] = (f, 'Count')
            
            return {'results': results}
        except redis.RedisError as e:
            raise MetricException(e)
