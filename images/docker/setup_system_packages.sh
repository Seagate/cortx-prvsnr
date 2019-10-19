#!/bin/bash

set -eux

# 'ip' tool is necessary for testinfra to explore interfaces
yum -y install iproute

rm -rf /var/cache/yum
