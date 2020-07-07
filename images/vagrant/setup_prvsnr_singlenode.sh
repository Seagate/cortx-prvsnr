#!/bin/bash

# assumptions:
# - current directory is a provisioner cli directory (TODO improve)

set -eux

prvsnr_src="${1:-rpm}"
prvsnr_release="${2-integration/centos-7.7.1908/last_successful}"  # empty value should be accepted as well

. ./common_utils/functions.sh

verbosity=2

# setup provisioner
install_provisioner "$prvsnr_src" "$prvsnr_release" '' '' '' true

# FIXME workaround
mkdir -p /opt/seagate/cortx/provisioner/cli
cp -R * /opt/seagate/cortx/provisioner/cli

configure_salt srvnode-1 '' '' '' true localhost

accept_salt_key srvnode-1

rm -rf /var/cache/yum
