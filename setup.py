# sauron's setup

from setuptools import setup

setup(
  name             = "sauron",
  packages         = ["sauron", "sauron.metrics", "sauron.emitters", "sauron.utils"],
  version          = "0.1.17",
  description      = "An eye for monitoring, and pushing monitoring data",
  author           = "Dan Lecocq",
  author_email     = "dan@seomoz.org",
  maintainer       = "Lasse Borchard", 
  maintainer_email = "lasse.borchard@prosiebensat1digital.de",
  url              = "http://github.com/johnny-die-tulpe/sauron/",
  keywords         = ["monitoring", "cloudwatch"],
  scripts          = ['bin/sauron-daemon'],
  data_files       = [('/etc/init.d', ['bin/sauron']),
                      ('/etc', ['sauron.yaml'])],
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
    "httplib2 >= 0.7.1",
    "argparse >= 1.2.1",
    "twisted",
    "redis",
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
