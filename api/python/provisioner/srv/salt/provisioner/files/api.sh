#!/bin/bash

set -eu

verbosity="${1:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

#   set access rights for api users
#       user file root
mkdir -p /opt/seagate/cortx/provisioner/srv_user
chown -R :prvsnrusers /opt/seagate/cortx/provisioner/srv_user
chmod -R g+rws /opt/seagate/cortx/provisioner/srv_user
setfacl -Rdm g:prvsnrusers:rwx /opt/seagate/cortx/provisioner/srv_user
#       user pillar
mkdir -p /opt/seagate/cortx/provisioner/pillar/user
chown -R :prvsnrusers /opt/seagate/cortx/provisioner/pillar/user
chmod -R g+rws /opt/seagate/cortx/provisioner/pillar/user
setfacl -Rdm g:prvsnrusers:rwx /opt/seagate/cortx/provisioner/pillar/user
