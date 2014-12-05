#!/bin/sh
[ -f /etc/init.d/sauron ] && /etc/init.d/sauron stop > /dev/null 2>&1 || true
/sbin/chkconfig --list sauron | grep -q sauron && /sbin/chkconfig --del sauron > /dev/null 2>&1 || true
