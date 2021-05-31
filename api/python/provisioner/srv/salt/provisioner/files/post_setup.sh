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


set -eu

verbosity="${1:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi


# set api
prvsnr_group=prvsnrusers
echo "Creating group '$prvsnr_group'..."
groupadd -f "$prvsnr_group"

shared_dir=/var/lib/seagate/cortx/provisioner/shared
factory_profile_dir="${shared_dir}/factory_profile"
prvsnr_locks_dir="${shared_dir}/locks"
user_srv_dir="${shared_dir}/srv"
user_srv_fileroot_dir="${user_srv_dir}/salt"
user_srv_pillar_dir="${user_srv_dir}/pillar"

seagate_log_dir=/var/log/seagate
prvsnr_log_dir="${seagate_log_dir}/provisioner"

# XXX EOS-17600 remove
user_srv_fileroot_dir_old=/opt/seagate/cortx/provisioner/srv_user   # FIXME deprecate that
user_srv_pillar_dir_old=/opt/seagate/cortx/provisioner/pillar/user  # FIXME deprecate that

echo "Creating group '$prvsnr_group'..."
groupadd -f "$prvsnr_group"

echo "Configuring access for provisioner data ..."
# TODO IMPROVE EOS-9581 consider to remove _old dirs someday
for path in "$factory_profile_dir" \
            "$prvsnr_locks_dir" \
            "$user_srv_fileroot_dir" \
            "$user_srv_pillar_dir" \
            "$prvsnr_log_dir" \
            "$user_srv_fileroot_dir_old" \
            "$user_srv_pillar_dir_old"; do
    mkdir -p "$path"
done

for path in "$user_srv_dir" \
            "$factory_profile_dir" \
            "$prvsnr_locks_dir" \
            "$seagate_log_dir" \
            "$prvsnr_log_dir" \
            "$user_srv_fileroot_dir_old" \
            "$user_srv_pillar_dir_old"; do
    if [[ "$path" == "$seagate_log_dir" ]]; then
        chmod o+rx "$path"
    else
        find "$path" -exec chown :"$prvsnr_group" {} \;
        if [[ "$path" == "$factory_profile_dir" ]]; then
            # profile is expected to be copied to user space before appliance
            find "$path" -exec chmod g+r {} \; -exec chmod g-w {} \;
        else
            find "$path" -exec chmod g+rw {} \;
            find "$path" -type d -exec chmod g+s {} \;  # TODO ??? might be not necessary since setfacl is used
            find "$path" -type d -exec setfacl -dm g:"$prvsnr_group":rwx {} \;
        fi
    fi
done
