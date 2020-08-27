#!/bin/bash
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing, 
# please email opensource@seagate.com or cortx-questions@seagate.com."
#


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
