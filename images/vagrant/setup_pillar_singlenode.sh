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
# please email opensource@seagate.com or cortx-questions@seagate.com.
#


# assumptions:
# - provisioner api is installed
# - current directory is a provisioner cli directory (TODO improve)

set -eux

mgmt_if="${1:-enp0s8}"
data_if="${2:-enp0s8}"
mgmt_device="${3:-/dev/sdb}"
data_device="${4:-/dev/sdc}"
release="${5:-integration/centos-7.7.1908/last_successful}"

# configure cluster.sls
pillar_file_tmp="$(realpath ./pillar.sls.tmp)"
default_gateway="$(ip route | grep default | head -1 | awk '{print $3}')"

bash ./configure -p cluster >"$pillar_file_tmp"
cat "$pillar_file_tmp"
sed -i "s~mgmt_if: .*~mgmt_if: $mgmt_if~g" "$pillar_file_tmp"
sed -i "s~data_if: .*~data_if: $data_if~g" "$pillar_file_tmp"
sed -i "s~/dev/sdb.*~$mgmt_device~g" "$pillar_file_tmp"
sed -i "s~/dev/sdc.*~$data_device~g" "$pillar_file_tmp"
sed -i "s~gateway: .*~gateway: $default_gateway~g" "$pillar_file_tmp"
cat "$pillar_file_tmp"
bash ./configure -vv -f "$pillar_file_tmp" cluster

bash ./configure -p release >"$pillar_file_tmp"
cat "$pillar_file_tmp"
sed -i "s~target_build: .*~target_build: $release~g" "$pillar_file_tmp"
cat "$pillar_file_tmp"
bash ./configure -vv -f "$pillar_file_tmp" release

rm -f "$pillar_file_tmp"
