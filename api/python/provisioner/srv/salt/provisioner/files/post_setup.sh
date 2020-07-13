#!/bin/bash

set -eu

verbosity="${1:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

prvsnr_group=prvsnrusers
install_dir=/opt/seagate/cortx/provisioner

shared_dir=/var/lib/seagate/cortx/provisioner/shared
factory_profile_dir="${shared_dir}/factory_profile"
user_srv_dir="${shared_dir}/srv"
user_srv_fileroot_dir="${user_srv_dir}/salt"
user_srv_pillar_dir="${user_srv_dir}/pillar"

seagate_log_dir=/var/log/seagate
prvsnr_log_dir="${seagate_log_dir}/provisioner"

user_srv_fileroot_dir_old=/opt/seagate/eos-prvsnr/srv_user   # FIXME deprecate that
user_srv_pillar_dir_old=/opt/seagate/eos-prvsnr/pillar/user  # FIXME deprecate that

echo "Configuring access for provisioner data ..."
# TODO IMPROVE EOS-9581 consider to remove _old dirs someday
for path in "$factory_profile_dir" \
            "$user_srv_fileroot_dir" \
            "$user_srv_pillar_dir" \
            "$prvsnr_log_dir" \
            "$user_srv_fileroot_dir_old" \
            "$user_srv_pillar_dir_old"; do
    mkdir -p "$path"
done

for path in "$user_srv_dir" \
            "$factory_profile_dir" \
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


#       Provisioning cli directory
chown -R :"$prvsnr_group" "${install_dir}/cli"
chmod -R 750 "${install_dir}/cli"
