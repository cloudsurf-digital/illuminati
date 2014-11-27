#!/bin/sh
[ -f /etc/init.d/sauron ] && /etc/init.d/sauron stop || true
/sbin/chkconfig --list sauron | grep -q sauron && /sbin/chkconfig --del sauron || true
