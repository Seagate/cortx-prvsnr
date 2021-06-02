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

NO_YUM_CLEAN="${NO_YUM_CLEAN:-}"

yum -y install  \
    git         \
    python36    \
    rpm-build   \
    yum-utils   \
    python3-devel \
    rpmdevtools \
    createrepo  \
    genisoimage
# Note. keep var cache here to speed up buildrpm.sh
# (yum-builddep will update the cache if missed each time)
# rm -rf /var/cache/yum

if [[ -z "$NO_YUM_CLEAN" ]]; then
    rm -rf /var/cache/yum
fi
