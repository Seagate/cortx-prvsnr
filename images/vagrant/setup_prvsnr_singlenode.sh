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
