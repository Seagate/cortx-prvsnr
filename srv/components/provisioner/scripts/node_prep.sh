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

set -euE
export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/node_prep.log}"
mkdir -p $(dirname "${LOG_FILE}")

PRVSNR_ROOT="/opt/seagate/cortx/provisioner"
localhost_ip="127.0.0.1"
minion_id="srvnode-0"
user_name=
uid=
group=
gid=
repo_url=


parse_args()
{

parse_args()
{
    echo "parse_args(): parsing input arguments" >> $LOG_FILE

    while [[ $# -gt 0 ]]; do
        case $1 in
            user)
                if [[ -z "$2" ]]; then
                    echo "Error: user name not provided" && exit 1;
                fi
                user_name=$2
                shift 2
                ;;
            uid)
                if [[ -z "$2" ]]; then
                    echo "Error: user id not provided" && exit 1;
                fi
                uid=$2
                shift 2
                ;;
            group)
                if [[ -z "$2" ]]; then
                    echo "Error: group name not provided" && exit 1;
                fi
                group=$2
                shift 2
                ;;
            gid)
                if [[ -z "$2" ]]; then
                    echo "Error: gid not provided" && exit 1;
                fi
                gid=$2
                shift 2
                ;;
            target-build)
                if [[ -z "$2" ]]; then
                    echo "Error: cortx build not provided" && exit 1;
                fi
                repo_url=$2
                shift 2
                ;;
            *) echo "Invalid option $1"; exit 1;;
        esac
    done
}

config_local_salt()
{

    # 1. Point minion to local host master in /etc/salt/minion 
    # 2. Restart salt-minion service
    # 3. Check if 'salt srvnode-0 test.ping' works

    if ! rpm -qa | grep -iEwq "salt|salt-master|salt-minion|cortx-prvsnr"; then
        echo "ERROR: salt packages not installed, please install salt and try again." | tee -a ${LOG_FILE}
        exit 1
    fi

    minion_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_master/files/master"
    master_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_minion/files/minion"

    yes | cp -f "${master_file}" /etc/salt/master
    yes | cp -f "${minion_file}" /etc/salt/minion

    local line_to_replace=$(grep -m1 -noP "master: " /etc/salt/minion|tail -1|cut -d: -f1)
    echo "Setting local-master in /etc/salt/minon" | tee -a ${LOG_FILE}
    yes | cp -f /etc/salt/minion /etc/salt/minion.bkp
    sed -i "${line_to_replace}s|^master:.*|master: ${localhost_ip}|" /etc/salt/minion
    echo "Done" | tee -a ${LOG_FILE}

    echo $minion_id > /etc/salt/minion_id

    echo "Restarting salt services" | tee -a ${LOG_FILE}
    systemctl start salt-master
    systemctl restart salt-minion
    echo "Done" | tee -a ${LOG_FILE}

    echo -e "\\nINFO: Waiting for key of $minion_id to become connected to salt-master"
    try=1; max_tries=10
    until salt-key --list-all | grep "srvnode-0" >/dev/null 2>&1
    do
        if [[ "\$try" -gt "$max_tries" ]]; then
            echo -e "\\nERROR: Key for salt-minion $minion_id not listed after $max_tries attemps."
            salt-key --list-all >&2
            exit 1
        fi
        try=\$(( \$try + 1 ))
        sleep 5
    done
    echo -e "\\nINFO: Key for $minion_id is listed."
    echo "Accepting the salt key for minion $minion_id"
    salt-key -y -a $_id

    # Check if salt '*' test.ping works
    echo "Waiting for minion to become ready" | tee -a ${LOG_FILE}
    try=1; max_tries=10
    until salt -t 1 $minion_id test.ping >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: minion srvnode-0 seems still not ready after $max_tries attempts." | tee -a ${LOG_FILE}
            #TODO: Retry after restarting services?
            exit 1
        fi
        try=$(( $try + 1 ))
    done
    echo "Minion on Server A started successfully" | tee -a ${LOG_FILE}
    fi
}

create_factory_user()
{
    user_name=$1
    uid=$2
    group=$3
    gid=$4

    echo "Creating user $user_name with uid:$uid, group:$group, gid:$gid" | tee -a ${LOG_FILE}
    groupadd -g ${gid} ${group}
    useradd -c "$user_name" -d /home/${user_name} -u ${uid} -g ${gid} -m ${user_name}
    echo "Done" | tee -a ${LOG_FILE}
}

install_cortx_pkgs()
{
    #repo="http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.8.2003/1291/prod/"
    repo=$1
    yum install -y yum-utils
    yum-config-manager --add-repo "${repo}/3rd_party/" 
    yum-config-manager --add-repo "${repo}/cortx_iso/"
    yum clean all

    #TODO: Remove once kickstart file is ready
    cortx_pkgs=(
        "java-1.8.0-openjdk-headless"
        "cortx-cli.x86_64"
        "python3 sshpass"
        "python36-m2crypto"
        "salt"
        "salt-master"
        "salt-minion"
        "cortx-prereq"
        "python36-cortx-prvsnr"
        "cortx-csm_agent.x86_64"
        "cortx-csm_web.x86_64"
        "cortx-ha.x86_64"
        "cortx-hare.x86_64"
        "cortx-libsspl_sec.x86_64"
        "cortx-libsspl_sec-method_none.x86_64"
        "cortx-libsspl_sec-method_pki.x86_64"
        "cortx-motr.x86_64"
        "cortx-motr-ivt.x86_64"
        "cortx-prereq.x86_64"
        "cortx-prvsnr.x86_64"
        "cortx-prvsnr-cli.x86_64"
        "cortx-py-utils.noarch"
        "cortx-s3server.x86_64"
        "cortx-sspl.noarch"
        "cortx-sspl-cli.noarch"
        "python36-cortx-prvsnr.x86_64"
        "stats_utils.x86_64"
        "udx-discovery.x86_64"
    )

    for pkg in ${cortx_pkgs[@]}; do
        echo "Installing $pkg" | tee -a ${LOG_FILE}
        rpm --quiet -qi $pkg ||  yum install --nogpgcheck -y $pkg  && \
            echo "Package $pkg is already installed."
    done
}


main()
{
    echo "Running prerequisite script" | tee -a ${LOG_FILE}
    parse_args $@
    if [[ ! -z $user_name ]]; then
        if [[ -z $uid -o -z $group -o $uid -o $gid ]]; then
            echo "Please provide uid, gid & group" | tee -a ${LOG_FILE}
            exit 1
        fi
        create_factory_user $user_name $uid $group $gid
    fi
    if [[ ! -z $repo_url ]]; then
        install_missing_pkgs $repo_url
    fi
    config_local_salt
}

main $@
echo "Done"
