#!/bin/bash
set -eux

yum install -y ruby-devel gcc make rpm-build rubygems python36

# issues with pip>=10:
# https://github.com/pypa/pip/issues/5240
# https://github.com/pypa/pip/issues/5221
python3 -m pip install -U pip setuptools

gem install --no-ri --no-rdoc rake fpm

rm -rf /var/cache/yum
