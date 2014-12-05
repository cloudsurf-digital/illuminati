#!/bin/sh
/sbin/chkconfig --add sauron > /dev/null 2>&1
/sbin/chkconfig --levels 345 sauron on > /dev/null 2>&1
