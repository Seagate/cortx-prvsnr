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
