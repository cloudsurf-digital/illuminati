#!/bin/sh
/sbin/chkconfig --add sauron > /dev/null
/sbin/chkconfig --levels 345 sauron on > /dev/null
