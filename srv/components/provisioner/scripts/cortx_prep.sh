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
ISO_CORTX_PATH="/opt/isos/cortx-*-single.iso"
ISO_OS_PATH="/opt/isos/cortx-os-*.iso"
nodejs_tar="http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/centos-7.8.2003/custom-build-1969/3rd_party/commons/node/node-v12.13.0-linux-x64.tar.xz"

usage()
{
    echo "
Usage: Usage: $0 [options]

Configure Cortx prerequisites locally.

General options:

Options:
  -t|--target-build BUILD_URL            Target Cortx build to deploy
"
}

parse_args()
{
    echo "parse_args(): parsing input arguments" >> $LOG_FILE

    while [[ $# -gt 0 ]]; do
        case $1 in
            target-build)
                if [[ -z "$2" ]]; then
                    echo "Error: URL for target cortx build not provided" && usage && exit 1;
                fi
                repo_url=$2
                shift 2
                ;;
            *) echo "Invalid option $1"; usage; exit 1;;
        esac
    done
}

config_local_salt()
{

    # 1. Point minion to local host master in /etc/salt/minion
    # 2. Restart salt-minion service
    # 3. Check if 'salt srvnode-0 test.ping' works

    if ! rpm -qa | grep -iEwq "salt|salt-master|salt-minion|cortx-prvsnr"; then
        echo "ERROR: salt packages are not installed, please install salt packages and try again." | tee -a ${LOG_FILE}
        exit 1
    fi

    minion_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_minion/files/minion_factory"
    master_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_master/files/master"

    yes | cp -f "${master_file}" /etc/salt/master
    yes | cp -f "${minion_file}" /etc/salt/minion

    #local line_to_replace=$(grep -m1 -noP "master: " /etc/salt/minion|tail -1|cut -d: -f1)
    #echo "Setting minion to local master in /etc/salt/minon" >> ${LOG_FILE}
    #yes | cp -f /etc/salt/minion /etc/salt/minion.bkp
    #sed -i "${line_to_replace}s|^master:.*|master: ${localhost_ip}|" /etc/salt/minion
    echo "Done" | tee -a ${LOG_FILE}

    echo $minion_id > /etc/salt/minion_id

    echo "Restarting the required services" | tee -a ${LOG_FILE}
    systemctl start salt-master
    systemctl restart salt-minion
    echo "Done" | tee -a ${LOG_FILE}

    echo "INFO: Waiting for key of $minion_id to become connected to salt-master" >> ${LOG_FILE}
    try=1; max_tries=10
    until salt-key --list-all | grep "srvnode-0" >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: Key for salt-minion $minion_id not listed after $max_tries attemps." >> ${LOG_FILE}
            echo "ERROR: Provisioner configuration manager failed for key acceptance" | tee -a ${LOG_FILE}
            salt-key --list-all >&2
            exit 1
        fi
        try=$(( $try + 1 ))
        sleep 5
    done
    echo "Key for $minion_id is listed." >> ${LOG_FILE}
    echo "Accepting the salt key for minion $minion_id" >> ${LOG_FILE}
    salt-key -y -a $minion_id

    # Check if salt '*' test.ping works
    echo "Waiting for Provisioner configuratoin manager to become ready" | tee -a ${LOG_FILE}
    try=1; max_tries=10
    until salt -t 1 $minion_id test.ping >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: minion srvnode-0 seems still not ready after $max_tries attempts." >> ${LOG_FILE}
            echo "ERROR: Provisioner configuration manager failed to connect to local server" | tee -a ${LOG_FILE}
            exit 1
        fi
        try=$(( $try + 1 ))
    done
    echo "Minion on Server A started successfully" >> ${LOG_FILE}
    echo "Done" | tee -a ${LOG_FILE}
}

create_factory_user()
{
    user_nodeadmin="nodeadmin"
    user_support="support"

    echo "Creating user: $user_nodeadmin" | tee -a ${LOG_FILE}
    #groupadd -g ${gid} ${group}
    useradd -c "$user_nodeadmin" -d /home/${user_nodeadmin}
    echo "Done" | tee -a ${LOG_FILE}

    echo "Creating user: $user_support" | tee -a ${LOG_FILE}
    #groupadd -g ${gid} ${group}
    useradd -c "$user_suport" -d /home/${user_support}
    echo "Done" | tee -a ${LOG_FILE}

}

setup_repos()
{
    #repo="http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.8.2003/1291/prod/"

    repo=$1
    yum install -y yum-utils
    echo "Configuring the repository: ${repo}/3rd_party" | tee -a ${LOG_FILE}
    yum-config-manager --add-repo "${repo}/3rd_party/"
    echo "Configuring the repository: ${repo}/cortx_iso" | tee -a ${LOG_FILE}
    yum-config-manager --add-repo "${repo}/cortx_iso/"

    yum clean all
}

install_cortx_pkgs()
{

    echo "Installing Cortx packages" | tee -a ${LOG_FILE}
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
        rpm --quiet -qi $pkg ||  yum install --nogpgcheck -y -q $pkg  && \
            echo "Package $pkg is already installed."
    done

    echo "Installing nodejs" | tee -a ${LOG_FILE}
    echo "Downloading nodeja tarball" >> ${LOG_FILE}
    wget ${nodejs_tar}
    echo "Extracting the tarball" >> ${LOG_FILE}
    mkdir /opt/nodejs
    tar -C /opt/nodejs/ -xvf node-v12.13.0-linux-x64.tar.xz
    echo "The extrracted tarball is kept at /opt/nodejs, removing the tarball ${nodejs_tar}" >> ${LOG_FILE}
    rm -rf ${nodejs_tar}

    echo "Done" | tee -a ${LOG_FILE}
}

download_isos()
{
    CORTX_RELEASE_REPO=$1
    echo "Downloading the ISOs" | tee -a ${LOG_FILE}
    mkdir /opt/isos
    cortx_iso=\$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's\/<\\/*[^>]*>\/\/g' | cut -f1 -d' ' | grep 'single.iso')
    curl -O ${CORTX_RELEASE_REPO}/iso/\${cortx_iso}
    os_iso=\$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's\/<\\/*[^>]*>\/\/g' | cut -f1 -d' '|grep  "cortx-os")
    curl -O ${CORTX_RELEASE_REPO}/iso/\${os_iso}
    #CORTX_PREP=\$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's\/<\\/*[^>]*>\/\/g' | cut -f1 -d' '|grep  ".sh")
    #curl -O ${CORTX_RELEASE_REPO}/iso/\${CORTX_PREP}
}

main()
{
    echo "Running Cortx-prep script" | tee -a ${LOG_FILE}
    parse_args $@
    #TODO: uncomment once ready
    #    create_factory_user $user_name $uid $group $gid
    if hostnamectl status | grep Chassis | grep -q server; then
        echo "This is Hardware" >> ${LOG_FILE}
        if systemctl list-units | grep scsi-network-relay; then
            systemctl start scsi-network-relay
        else
            echo "ERROR scsi-network-relay service is not present" | tee -a ${LOG_FILE}
            exit 1
        fi
        if [[ ! -z $repo_url ]]; then
            # User has provided target-build for HW
            # Remove the ISOs set up by Kickstart
            # download the iso from provided build url
            # mount the iso
            
            #echo "Removing the ISOs setup by Kickstart" | tee -a ${LOG_FILE}
            #TODO:
                #remove_isos
                #download_isos $repo_url
                #mount_isos
                #configure repos from iso files

            #WORKAROUND: Use hosted repos until download_isos function is ready
            setup_repos $repo_url
        else
            echo "Using the ISO files set up by kickstart " >> ${LOG_FILE}
            #TODO: use the same isos downloaded by KS file to install the packages
            # configure repos from iso files

            echo "ERROR: Please provide the target-build unless kickstart file is in place" | tee -a ${LOG_FILE}
            exit 1
        fi
    else
        echo "This is VM" >> ${LOG_FILE}
        if [[ ! -z $repo_url ]]; then
            setup_repos $repo_url
        else
            echo "ERROR: target-build not provided, it's mandetary option for VM"
            echo "ERROR: Please provide the target-build " | tee -a ${LOG_FILE}
            exit 1
        fi
    fi
    install_cortx_pkgs
    config_local_salt


    if command -v cortx_setup; then
        echo "Preparing the Cortx ConfStore with default configuration" | tee -a ${LOG_FILE}
        cortx_setup prepare_confstore
    else
        echo "WARNING: cortx_setup commands are not installed" | tee -a ${LOG_FILE}
        echo "Please install the cortx_setup commands and run: 'cortx_setup prepare_confstore' manually"
    fi
}

main $@
echo "Done"