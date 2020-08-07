#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

#!/bin/bash

# assumptions:
# - provisioner api is installed
# - current directory is a provisioner cli directory (TODO improve)

set -eux

mgmt_if="${1:-enp0s8}"
data_if="${2:-enp0s8}"
mgmt_device="${3:-/dev/sdb}"
data_device="${4:-/dev/sdc}"
cortx_release="${5:-integration/centos-7.7.1908/last_successful}"

# configure cluster.sls
pillar_file_tmp="$(realpath ./pillar.sls.tmp)"
default_gateway="$(ip route | grep default | head -1 | awk '{print $3}')"

bash ./configure-eos -p cluster >"$pillar_file_tmp"
cat "$pillar_file_tmp"
sed -i "s~mgmt_if: .*~mgmt_if: $mgmt_if~g" "$pillar_file_tmp"
sed -i "s~data_if: .*~data_if: $data_if~g" "$pillar_file_tmp"
sed -i "s~/dev/sdb.*~$mgmt_device~g" "$pillar_file_tmp"
sed -i "s~/dev/sdc.*~$data_device~g" "$pillar_file_tmp"
sed -i "s~gateway: .*~gateway: $default_gateway~g" "$pillar_file_tmp"
cat "$pillar_file_tmp"
bash ./configure-eos -vv -f "$pillar_file_tmp" cluster

bash ./configure-eos -p release >"$pillar_file_tmp"
cat "$pillar_file_tmp"
sed -i "s~target_build: .*~target_build: $cortx_release~g" "$pillar_file_tmp"
cat "$pillar_file_tmp"
bash ./configure-eos -vv -f "$pillar_file_tmp" release

rm -f "$pillar_file_tmp"
