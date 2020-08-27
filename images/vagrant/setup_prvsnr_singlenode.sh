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
