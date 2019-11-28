#!/bin/bash
set -eux

yum -y install git python36 rpm-build yum-utils
rm -rf /var/cache/yum
