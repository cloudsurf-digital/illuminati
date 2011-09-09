Sauron
======

Sauron is meant to act as an all-seeing eye for pushing data to CloudWatch. It
works based on extendable "metrics", which are just python classes that report
back values. For example, it comes with metrics to monitor disk space, mysql
health, pinging servers, etc.

This is very early days, and mechanisms will likely change slightly. In the mean
time, this is the state of affairs.

Running
-------

Soon we'll have a little init.d script, but for the time being, just run reporter.py
as either nohup or with screen.

Configuration
=============

Store your configuration file in either ./sauron.conf or /etc/sauron.conf, in conf-
style format. Each section can be the name of a metric, and then the paramters
specific to that metric. All metrics at least include a name, which must be provided
in the configuration file, next to the metric name as in "metric:name". There also 
__must__ be a section called "sauron," which specifies the interval (in seconds) that 
should be used in between running the metrics. Optionally, you can provide a "namespace"
parameter, which is what the custom metrics are reported under. If you don't provide it,
it uses the hostname of the system running it. For example:

	[sauron]
	interval = 60

	[DiskMetric:root]
	path = /
	keys = percent,inodes

	[MySQLMetric:mysql]
	host = localhost
	user = dan
	passwd = somepassword

	[SphinxMetric:sphinx]

Metrics
=======

Here's a brief rundown of the included metrics

Disk
----

Can check up on disk free space, number of inodes in use, etc.

LogMetric _[New]_
-----------------

"Tails" a log file that you specify to count the number of lines that match the provided
regular expressions. It remembers where it last read in the file (except between restarts),
and continues reading from there. It knows when the file has been replaced (or more exactly,
when the inode for the provided path changes). It only actually reads from the file when
the modification time for the file changes (st\_mtime). For example, if you want to track
the number of successes and failures listed in a log file:

	[LogMetric:myServiceLog]
	path = /var/log/myService.log
	success = ^Success
	failure = failed$

MySQL
-----

Runs 'SHOW STATUS' on mysql on the host provided, using the user and password provided.

PingMetric
----------

Pings a url, with a configurable url, optional data string (should be url-encoded), and
optional timeout. Returns the latency, with the assumption being that high failure leads
to INSUFFICIENT\_DATA in CloudWatch

PipeMetric _[New]_
------------------

Similar to "LogMetric," this "tails" a named pipe and matches each line against a set of
provided regular expressions. The advantage of the PipeMetric is that if you don't intend
to keep your files long-term, you can get performance boosts that come with using a named
pipe instead of a file. If there isn't a fifo already created in the specified path, it will
create one for you:

	[PipeMetric:myServiceLog]
	path = /var/log/namedPipeMyService.log
	success = ^Success
	failure = failed$

ProcMetric _[New]_
------------------

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

You can specify the specific attributes you would like pushed to CloudWatch, in case you
don't want all of these cluttering your monitoring (and costing you money). To do so, just
specify the 'keys' argument in the configuration file, as a comma-separated list. By way of
some examples, you might want to make sure that you always have a process 'myService' being
run as user 'me', in the directory '/var/me'. And in this case, you're really just interested
in how much memory it's using, as well as how many threads it has going at any one time:

	[ProcMetric:myService]
	user = me
	cwd  = /var/me
	keys = threads,percent-mem,real-mem

ShellMetric
-----------

Executes a shell command that returns a number. __This is potentially dangerous, as it
allows for injection attacks, so use at your own risk.__ To alleviate this risk, you can
either run reporter.py under its own user, or just remove metrics/ShellMetric.py.
Specify the command to run, and the units:

	[ShellMetric:files]
	cmd = ls -lah | wc -l
	units = Count

SphinxMetric
------------

Tests the health of a sphinx instance by running 'SHOW STATUS' on the searchd instance.

SystemMetric
------------

Meant to be general stats about the system, but currently just makes system-wide physical
and virtual memory consumption available.

Extensibility
=============

Each metric is expected to return a dictionary, containing at least one key,
"results," which is another dictionary mapping names of statistics to a tuple
of the value and units. Perhaps it's better to just show by example!

	return { 'results' : {
			'latency'   : (latency, 'Seconds'),
			'something' : (value, 'Kilobytes')
		}
	}

If you do extend the available metrics, inherit from the metric class, and implement
the "values," function to return a dictionary in the above style. Optionally, 
supply another key in that dictionary which is the time for which the data is
valid. __Your metric "MyMetric" should be stored in metrics/MyMetric.py__