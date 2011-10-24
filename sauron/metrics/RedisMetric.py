#! /usr/bin/env python

import redis
import Metric

class RedisMetric(Metric.Metric):
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
		Metric.Metric.__init__(self, name)
		self.reconfig(name, **kwargs)
	
	def reconfig(self, name, **kwargs):
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
			with self.redis.pipeline() as pipe:
				for g in self.get:
					pipe.get(g)
				for l in self.llen:
					pipe.llen(l)
				for h in self.hlen:
					pipe.hlen(h)
				for k,v in self.hget.items():
					pipe.hget(k, v)
				for s in self.scard:
					pipe.scard(s)
				fetched = pipe.execute()
				for index in range(len(fetched)):
					results[both[index]] = (fetched[index], 'Count')

			return {'results': results}
		except redis.RedisError as e:
			raise Metric.MetricException(e)
