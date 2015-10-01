Sauron
======

Sauron is meant to act as an all-seeing eye for pushing data to monitoring. It
works based on extendable "metrics", which are just python classes that report
back values. For example, it comes with metrics to monitor disk space, mysql
health, pinging servers, etc. These metrics are then pushed to "emitters" which
describe where that data should go. Multiple emitters can be used, and are meant
to be interchangeable.

Installation
------------

Install with pip or easy\_install, or install from git:

	sudo pip install sauron
	# Or, installing from git
	git clone git@github.com:seomoz/sauron.git
	cd sauron && sudo python setup.py install
        # or build rpm on CentOs, AmazonLinux, Redhat
	sudo yum group install "Development tools"
	git clone https://github.com/johnny-die-tulpe/sauron.git
	cd sauron && python setup.py bdist_rpm; cd -
	sudo yum localinstall sauron/dist/sauron-*.noarch.rpm

Running
-------

If you'd like to run sauron straight-up without daemonizing (for example for 
testing your configuration):

	# Attempt to gather all your stats, without sending anywhere
	sauron-daemon --dry-run

Instead, if you'd like to daemonize (pid file in /var/run/sauron.pid)

	# Start it or stop it
	sauron start
	sauron stop
	# Since sauron re-reads the configuration file automatically,
	# this is only necessary between sauron upgrades
	sauron restart

Dependencies
============

The only dependencies for sauron itself:

* __python__
* __pyyaml__ is used for reading configuration files

Metric dependencies:

* __psutil__ Is used for __SystemMetric__, __ProcMetric__
* __mysql-python__ Is used for __SphinxMetric__, __MySQLMetric__

Emitter dependencies:

* __boto__ Version 2.0+ is used for __CloudWatch__. That's the current release at
time of writing, but if you have boto 1.9, you'll need to upgrade.
* __tweepy__ is used for the __Twitter__ emitter.
* __httplib2__ is used for the __HTTPEndpoint__ emitter, __NginxServerStatusMetric__ and
__HttpdServerStatus metric__.

Installing Dependencies
-----------------------

Dependencies are automatically installed with sauron, but if for whatever reason you
have trouble, you can install them manually

	sudo easy_install boto
	sudo easy_install pyyaml
	sudo easy_install psutil
	sudo easy_install tweepy
	sudo easy_install httplib2
	sudo easy_install mysql-python

Configuration
=============

Store your configuration file in either `./sauron.yaml` or `/etc/sauron.yaml`, in YAML-
style format. Each section can be the name of a metric, and then the paramters
specific to that metric. All metrics at least include a name, which must be provided
in the configuration file, as a key in the metrics dictionary and then a module. The
rest of the arguments are specific to the particular metric.

System-wide configuration is just the interval and the path to the log file. Emitters
represent the destinations to which you want to push.

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

Emitters are responsible for taking stats that have been gathered, and doing something
with them. Whether that's to send them along to another computer or store them for later
queries, each emitter gets to handle the metrics in its own way. For more detailed
information, refer to the emitters' README.md. __Emitters are easily extensible__, Currently
included emitters are:

* CloudWatch (for reporting to Amazon's [CloudWatch](http://aws.amazon.com/cloudwatch/))
* Twitter (tweets each of the gathered metrics)

Others are in the works, including support for:

* Sending to HTTP endpoints in JSON or XML
* Making stats and graphs available through a campfire bot
* Making stats and graphs available through Jabber

Metrics
=======

Metrics are python classes that know how to gather particular pieces of information, and
then return those as a dictionary that is then sent to all the emitters configured. Like
emitters, __metrics are easily extensible__, so if there's something you'd like to be able
to monitor that you can access in python, you can write a little bit of python and track it!
For more thorough documentation, see the metrics' README.md. Currently included metrics are:

* Disk metrics (track free space, free inodes, etc.)
* Log metric (follows log files for lines that match regexes you provide)
* __MySQL metric__ (track stats from `SHOW STATUS`)
* __JSON ping metric__ (tracks the values of a json associative array reported by a HTTP endpoint)
* Ping metric (pings a url and reports latency)
* Pipe metric (identical to the log metric, except designed to work with named pipes)
* __Proc metric__ (tracks stats associated with a specific process or set of processes)
* __Redis metric__ (stats from `info` command, values in keys you specify, queue lengths, etc.)
* S3Bucket metric (number and age of keys in a bucket)
* __Shell metric__ (tracks the value returned by a specified shell command)
* Sphinx metric (tracks statistics about a (Sphinx)[http://sphinxsearch.com/] index)
* __System metric__ (information about the system as a whole, like memory consumption)
* __HttpdServerStatus metric__ (information about the apache server-status handler)
* __NginxServerStatusMetric__ (data from ngx_http_stub_status_module)


Roadmap
=======

* We'd like to provide a default monitoring server and interface. Maybe not something that's
amazing, but at least something to get started.
	- Notifications for nodes first reporting in
	- Notifications for nodes ceasing to report in
* Unit testing
* Graph injection for bots
* Reconfig support for emitters

Design Questions
================

* When we list actions in the configuration file, should we _delete_ subscriptions that don't
appear in the listed subscriptions? Maybe just a warning?
