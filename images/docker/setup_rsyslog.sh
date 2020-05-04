#!/bin/bash
set -eux

yum -y install rsyslog
rm -rf /var/cache/yum
