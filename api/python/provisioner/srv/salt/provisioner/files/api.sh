#!/bin/bash

set -eu

verbosity="${1:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

#   set access rights for api users
#       user file root
mkdir -p /opt/seagate/eos-prvsnr/srv_user
chown -R :prvsnrusers /opt/seagate/eos-prvsnr/srv_user
chmod -R g+rws /opt/seagate/eos-prvsnr/srv_user
setfacl -Rdm g:prvsnrusers:rwx /opt/seagate/eos-prvsnr/srv_user
#       user pillar
mkdir -p /opt/seagate/eos-prvsnr/pillar/user
chown -R :prvsnrusers /opt/seagate/eos-prvsnr/pillar/user
chmod -R g+rws /opt/seagate/eos-prvsnr/pillar/user
setfacl -Rdm g:prvsnrusers:rwx /opt/seagate/eos-prvsnr/pillar/user
