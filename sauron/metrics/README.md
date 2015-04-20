Metrics
=======

Metrics are python classes that know how to gather particular pieces of information, and
then return those as a dictionary that is then sent to all the emitters configured. Like
emitters, __metrics are easily extensible__, so if there's something you'd like to be able
to monitor that you can access in python, you can write a little bit of python and track it!
Currently included metrics are:

Disk
----

Can check up on disk free space, number of inodes in use, etc.

LogMetric
---------

"Tails" a log file that you specify to count the number of lines that match the provided
regular expressions. Alternatively, you can use the _last_ group of the regular expression
as a number, which is what will be returned. It remembers where it last read in the file
(except between restarts), and continues reading from there. It knows when the file has
been replaced (or more exactly, when the inode for the provided path changes). It only
actually reads from the file when the modification time for the file changes (st\_mtime).
For example, if you want to track the number of successes and failures listed in a log file:

	myServiceLog:
		module: LogMetric
		path: /var/log/myService.log
		success: ^Successfully fetched (\d+)
		failure: failed$

MySQLMetric
-----------

Runs 'SHOW STATUS' on mysql on the host provided, using the user and password provided.

PingMetric
----------

Pings a url, with a configurable url, optional data string (should be url-encoded), and
optional timeout. Returns the latency, with the assumption being that high failure leads
to INSUFFICIENT\_DATA in CloudWatch

PipeMetric
----------

Similar to "LogMetric," this "tails" a named pipe and matches each line against a set of
provided regular expressions. The advantage of the PipeMetric is that if you don't intend
to keep your files long-term, you can get performance boosts that come with using a named
pipe instead of a file. If there isn't a fifo already created in the specified path, it will
create one for you:

	myServiceLog:
		module: PipeMetric
		path: /var/log/namedPipeMyService.log
		success: ^Success
		failure: failed$

ProcMetric
----------

Some of the functionality provided in this metric is limited by the underlying OS, but it
uses [psutil](http://code.google.com/p/psutil/) to try to get away from OS differences.
Still, psutil is a work in progress, and doesn't have support for everything yet.

ProcMetric actually lets you search for particular processes and get aggregate stats on all
the processes that match. Typically, you'll want to limit it to a particular process (or
perhaps the same processes repeated several times). Each filter is considered a regular
expression, that matches if it is found anywhere in the corresponding process property:

* __name__ - __Required__ The name of the process. For scripts, this is the name of the __interpreter__
* __user__ - The username of the user running that process
* __args__ - Args provided to the process when invoked. For scripts, includes the script name
* __cwd__  - The current working directory of the running process

This metric __always__ returns a count of the number of processes that match your description,
and if processes match, it aggregates the following statistics (summing them up across all procs):

* __user-cpu__ - Time spent in user (s)
* __sys-spu__  - Time spend in sys (s)
* __uptime__   - How long the process has been running (s)
* __real-mem__ - Real memory consumption (MB)
* __virt-mem__ - Virtual memory consumption (MB)
* __percent-mem__ - Portion of total memory consumption (percent)
* __children__ - Number of child processes (count)
* __threads__  - Number of threads (count)
* __files__    - Number of files it has open (count)
* __connections__ - Number of TCP/UDP connections (count)

You can specify the specific attributes you would like pushed, in case you
don't want all of these cluttering your monitoring (and/or costing you money). To do so, just
specify the 'keys' argument in the configuration file, as a list. By way of
some examples, you might want to make sure that you always have a process 'myService' being
run as user 'me', in the directory '/var/me'. And in this case, you're really just interested
in how much memory it's using, as well as how many threads it has going at any one time:

	myService:
		module: ProcMetric
		user: me
		cwd: /var/me
		keys:
			- threads
			- percent-mem
			- real-mem

RedisMetric _[New]_
-------------------

This metric can gather all the statistics provided from Redis' `info` command, as well
as the number of items in various lists, hashes, set, as well as values stored in various
keys. All the configuration options follow their redis command equivalents, and fetches
from the redis server are pipelined. For example, if you use redis lists as queues, and
also keep track of stats in specific keys:

	redis:
	    module: RedisMetric
			# The host, password and port are optional, and default
			# to `localhost`, None, and `6379` respectively
	    host: my-redis-server
	    password: mySecretPassword
	    port: 6379
	    # The keys we want to save from Redis' info command
	    info:
	        - uptime_in_seconds
	        - used_cpu_sys
	        - used_cpu_user
	        - used_memory
	        - mem_fragmentation_ratio
	        - changes_since_last_save
	        - total_commands_processed
	    # The keys we should get, and interpret as a number
	    get:
	        - stats-jobs-finished
	        - stats-jobs-failed
	    # The keys we should lookup and get the length of
	    llen:
	        - queue-work
	        - queue-finished
	        - queue-failed
	    # How many keys are in the myhash hash?
	    hlen:
	        - myhash
	    # Report the wins and losses keys of the stats hash
	    hget:
	        stats: wins
	        stats: losses
	    # How many elements are in this particular set
	    scard:
	        - myset

RabbitMQMetric _[New]_
-----------------------

This metric can gather the statistics of queues you selected from RabbitMQ management
plugin API. This statistics are mainly containing rate information of messaging like
publishing, unacknowleged and all of messages. If you did not changed the settings of
the management plugin, you don't need touch the settings of host, port, user and
password. If you changed this, you have to set these settings by your self:

    rabbitmq:
        module: RabbitMQMetric
        queues:
            - first_queue
            - second_queue

S3BucketMetric _[New]_
----------------------

Looks up the number and maximum age of keys in a given bucket

ShellMetric
-----------

Executes a shell command that returns a number. __This is potentially dangerous, as it
allows for injection attacks, so use at your own risk.__ To alleviate this risk, you can
either run reporter.py under its own user, or just remove metrics/ShellMetric.py.
Specify the command to run, and the units:

	files:
		module: ShellMetric
		cmd: ls -lah | wc -l
		units: Count

SphinxMetric
------------

Tests the health of a sphinx instance by running 'SHOW STATUS' on the searchd instance.

SystemMetric
------------

Meant to be general stats about the system, but currently just makes system-wide physical
and virtual memory consumption available.

TimeMetric
-----------
Very simple metric that will simple set a value of 1 between the start and end time.
This can be used to work around Issues with Amazons Scheduled Scaling by creating 
Cloudwatch Alarms based upon this metric.
Sample:

       module: TimeMetric
       start: '12:00'
       stop:  '13:00'

HttpdServerStatus
------------

###Describtion

You can choose between the following data metrics from httpd server-status handler:
 * CPULoad
 * ReqPerSec
 * BytesPerSec
 * BusyWorkers
 * IdleWorkers
 * FreeClients

The FreeClients Metric is a count of empty client slots (ServerLimit - Busyworkers)


###Configuration Example

sauron.yaml

    apache:
        module: HttpdServerStatus
        url: http://localhost/server-status?auto
        metrics: 
         - FreeClients
         - BusyWorkers

Extensibility
=============

Each metric is instantiated with a name, and then all the options associated with it in
the configuration file. Because sauron also re-reads the configuration files after they
have changed, you must also implement a second method, `reconfig`, that can be called
repeatedly with different options without leaking resources or doing unnecessarily much
work. For most metrics, this is relatively easy (taken from JSONPingMetric):

	def __init__(self, name, **kwargs):
		Metric.__init__(self, name)
		self.reconfig(name, **kwargs)

	def reconfig(self, name, url, post=None, timeout=30):
		self.name = name
		self.url  = url
		self.post = post
		self.timeout = timeout

Often it's just a matter of saving the configuration options provided. In some cases, though,
the initial instantiation of a metric can require allocation of some resources, so it's
important to not allocate resources unnecessarily with repeated calls to `reconfig`.

Each metric is also expected to provide a method, `values` that returns a dictionary
containing at least one key, `results`, which is a dictionary of the names of each stat
to track, and its units. Perhaps it's better to show by example:

	def values(self):
		# So some work here
		# ...
		return { 'results' : {
				'latency'   : (latency, 'Seconds'),
				'something' : (value, 'Kilobytes')
			}
		}

The only other constraint is that your metric __should catch all internal errors, and
raise a MetricException if it's a legitimate failure.__ Sauron won't fail otherwise,
but it's considered the expected behavior. For examples, reference any of the included
metrics.
