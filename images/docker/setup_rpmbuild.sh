#!/bin/bash
set -eux

yum -y install git python36 rpm-build yum-utils python3-devel
# Note. keep var cache here to speed up buildrpm.sh
# (yum-builddep will update the cache if missed each time)
# rm -rf /var/cache/yum
