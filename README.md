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
in the configuration file. There also __must__ be a section called "sauron," which
specifies the interval (in seconds) that should be used in between running the metrics.
Optionally, you can provide a "namespace" parameter, which is what the custom metrics
are reported under. If you don't provide it, it uses the instance-id of the the machine
running it. For example:

	[sauron]
	interval = 60

	[DiskMetric]
	name = root
	path = /
	keys = percent,inodes

	[MySQLMetric]
	name = mysql
	host = localhost
	user = dan
	passwd = somepassword

	[SphinxMetric]
	name = sphinx

Metrics
=======

Here's a brief rundown of the included metrics

Disk
----

Can check up on disk free space, number of inodes in use, etc.

MySQL
-----

Runs 'SHOW STATUS' on mysql on the host provided, using the user and password provided.

PingMetric
----------

Pings a url, with a configurable url, optional data string (should be url-encoded), and
optional timeout. Returns the latency, with the assumption being that high failure leads
to INSUFFICIENT\_DATA in CloudWatch

ShellMetric
-----------

Executes a shell command that returns a number. __This is potentially dangerous, as it
allows for injection attacks, so use at your own risk.__ To alleviate this risk, you can
either run reporter.py under its own user, or just remove metrics/ShellMetric.py.
Specify variable names, and then the associated units as such:

	[ShellMetric]
	num_files = ls -lah | wc -l
	num_files-units = Count
	variable = ...
	variable-units = Kilobytes

SphinxMetric
------------

Tests the health of a sphinx instance by running 'SHOW STATUS' on the searchd instance.

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