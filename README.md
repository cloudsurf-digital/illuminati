Sauron
======

Sauron is meant to act as an all-seeing eye for pushing data to monitoring. It
works based on extendable "metrics", which are just python classes that report
back values. For example, it comes with metrics to monitor disk space, mysql
health, pinging servers, etc. These metrics are then pushed to "emitters" which
describe where that data should go. Multiple emitters can be used, and are meant
to be interchangeable.

Running
-------

Soon we'll have a little init.d script, but for the time being, just run reporter.py
as either nohup or with screen.

Configuration
=============

Store your configuration file in either ./sauron.yaml or /etc/sauron.yaml, in YAML-
style format. Each section can be the name of a metric, and then the paramters
specific to that metric. All metrics at least include a name, which must be provided
in the configuration file, as a key in the metrics dictionary and then a module. The
rest of the arguments are specific to the particular metric.

System-wide configuration is just the interval and the path to the log file. Emitters
represent the destinations to which you want to push. Currently, only CloudWatch is
supported, but I hope to implement more soon.

	interval:   60
	logfile:    sauron.log

	# Emitters are where you want to publish the data
	emitters:
	    # For example, we support CloudWatch
	    CloudWatch:
	        namespace: sauron

	# Metrics are what you want to collect
	metrics:
	    # This logs the percent usage and the number of
	    # free inodes on the volume mounted at /
	    root:
	        module: DiskMetric
	        path: /
	        keys: 
	            - percent
	            - inodes

	    # This looks at the apache access log, and counts
	    # the number of lines that match [POST], [GET]
	    apache:
	        module: LogMetric
	        path: /var/log/apache2/access.log
	        post: \[POST\]
	        get: \[GET\]

Emitters
========

Currently, we only support CloudWatch, but we'd like that to change.

CloudWatch _[New]_
------------------

To use CloudWatch, you must have ~/.boto set up with your AWS Identity and Secret keys.
You must also then specify a namespace for your metrics, and optionally additional dimensions.
If you are running sauron on an EC2 instance, it will automatically include the instance-id
in the dimensions.

[__CloudWatch Alarms__](http://aws.amazon.com/documentation/cloudwatch/) can now be baked into
the configuration of the CloudWatch emitter. For example, suppose you want to watch to make 
sure that an apache process is running at all times. You could configure a ProcMetric to match
the appropriate process configuration. Then, you'd add an __action__ to CloudWatch, and an 
__alarm__ that executes that action when certain conditions on that metric are reached:

	# For example, we support CloudWatch
	CloudWatch:
    namespace: ...
    actions:
        emailAdmin:
            - {endpoint: my@email.com}
    alarms:
        serverDied:
            description: Oh noes! Apache fell over!
            metric: apache-count
            threshold: 0
            comparison: <=
            alarm:
                - emailAdmin
            insufficient_data:
                - emailAdmin

	# Counts the number of apache processes
	apache:
		module: ProcMetric

The CloudWatch Alarm API is perhaps a little complex, but we wanted our configuration to reflect
it closely. You can provide the actions to take when the alarm is in the INSUFFICIENT\_DATA state,
(which can be a good indication that either monitoring or the machine died), ALARM, and OK (which
doesn't necessarily seem like a useful state, but it's available in the API). You can also include
the dimensions across which you'd like to gather data, but we imagine you'd often like to watch
on a per-instance basis.

Metrics
=======

Here's a brief rundown of the included metrics

Disk
----

Can check up on disk free space, number of inodes in use, etc.

LogMetric _[New]_
-----------------

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

	myServiceLog:
		module: PipeMetric
		path: /var/log/namedPipeMyService.log
		success: ^Success
		failure: failed$

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

Roadmap
=======

* We'd like to provide a default monitoring server and interface. Maybe not something that's
amazing, but at least something to get started.
	- Notifications for nodes first reporting in
	- Notifications for nodes ceasing to report in
* Chatbot emitter to provide graphs, statuses, etc.
* Add daemonizing, startup, shutdown, etc.
* Unit testing

Design Questions
================

* When we list actions in the configuration file, should we _delete_ subscriptions that don't
appear in the listed subscriptions? Maybe just a warning?