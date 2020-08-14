#!/bin/bash
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


set -eux

pip3_package="$(repoquery --qf='%{name}' --pkgnarrow=all 'python3-pip' | head -n1)"

if [[ -z "$pip3_package" ]]; then
    pip3_package="$(repoquery --qf='%{name}' --pkgnarrow=all 'python36-pip')"
fi

if [[ -z "$pip3_package" ]]; then
    >&2 echo "Package for pip3 is not found"
    exit 1
fi

yum install -y "$pip3_package"
