# sauron's setup

from setuptools import setup

setup(
	name             = "sauron",
	packages         = ["sauron", "sauron.metrics", "sauron.emitters"],
	version          = "0.1.0",
	description      = "An eye for monitoring, and pushing monitoring data",
	author           = "Dan Lecocq",
	author_email     = "dan@seomoz.org",
	url              = "http://github.com/seomoz/sauron/",
	keywords         = ["monitoring", "cloudwatch"],
	scripts          = ['bin/sauron-daemon', 'bin/sauron'],
	classifiers      = [
		"Programming Language :: Python",
		"Intended Audience :: Developers",
		"Topic :: Software Development :: Libraries :: Python Modules"
	],
	install_requires = [
		"PyYAML >= 3.10",
		"psutil >= 0.3.0",
		"pymysql >= 0.4",
		"boto >= 2.0",
		"tweepy >= 1.7.1",
		"httplib2 >= 0.7.1"
	],
	long_description = """\
Sauron is meant to act as an all-seeing eye for pushing data to monitoring. It
works based on extendable "metrics", which are just python classes that report
back values. For example, it comes with metrics to monitor disk space, mysql
health, pinging servers, etc. These metrics are then pushed to "emitters" which
describe where that data should go. Multiple emitters can be used, and are meant
to be interchangeable.
"""
)