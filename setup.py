# sauron's setup

from distutils.core import setup
setup(
    name = "sauron",
    packages = ["sauron"],
    version = "0.1.0",
    description = "An eye for monitoring, and pushing monitoring data",
    author = "Dan Lecocq",
    author_email = "dan@seomoz.org",
    url = "http://github.com/seomoz/sauron/",
    download_url = "http://chardet.feedparser.org/download/python3-chardet-1.0.1.tgz",
    keywords = ["monitoring", "cloudwatch"],
    classifiers = [
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules"
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