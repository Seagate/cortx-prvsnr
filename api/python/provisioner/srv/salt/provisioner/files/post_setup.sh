#!/bin/bash

set -eu

verbosity="${1:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

prvsnr_group=prvsnrusers
srv_dir=/var/lib/seagate/cortx/provisioner/srv
srv_dir_fileroot="${srv_dir}/salt"
srv_dir_pillar="${srv_dir}/pillar"
srv_dir_fileroot_old=/opt/seagate/eos-prvsnr/srv_user
srv_dir_pillar_old=/opt/seagate/eos-prvsnr/pillar/user
log_dir=/var/log/seagate/provisioner

echo "Configuring access for provisioner data ..."
# TODO IMPROVE EOS-9581 consider to remove _old dirs someday
for path in "$srv_dir_fileroot" "$srv_dir_pillar" "$srv_dir_fileroot_old" "$srv_dir_pillar_old" "$log_dir"; do
    mkdir -p "$path"
    find "$path" -exec chown :"$prvsnr_group" {} \; -exec chmod g+rw {} \;
    find "$path" -type d -exec chmod g+s {} \;  # TODO ??? might be not necessary since setfacl is used
    find "$path" -type d -exec setfacl -dm g:"$prvsnr_group":rwx {} \;
done

#       Provisioning cli directory
chown -R :"$prvsnr_group" /opt/seagate/eos-prvsnr/cli
chmod -R 750 /opt/seagate/eos-prvsnr/cli
