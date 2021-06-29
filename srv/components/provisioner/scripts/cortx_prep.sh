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
minion_id="srvnode-0"
salt_opts="--no-color --out-file=$LOG_FILE --out-file-append"
repo_url=
nodejs_tar="http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/centos-7.8.2003/custom-build-1969/3rd_party/commons/node/node-v12.13.0-linux-x64.tar.xz"

_usage()
{
    echo "
Options:
  -t|--target-build BUILD_URL        Target Cortx build to deploy
"

}

usage()
{
    echo "
Usage: Usage: $0 [options]
Configure Cortx prerequisites locally.
"
    _usage
}

parse_args()
{
    echo "DEBUG: parse_args(): parsing input arguments" >> $LOG_FILE

    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--target-build)
                set +u
                if [[ -z "$2" ]]; then
                    echo "Error: URL for target cortx build not provided"
                    _usage
                    exit 1
                fi
                set -u
                repo_url=$2
                shift 2
                ;;
            -h|--help)
                usage; exit 0;;
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
        echo "ERROR: salt packages are not installed, please install salt packages and try again." | tee -a "${LOG_FILE}"
        exit 1
    fi

    minion_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_minion/files/minion_factory"
    master_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_master/files/master"

    yes | cp -f "${master_file}" /etc/salt/master
    yes | cp -f "${minion_file}" /etc/salt/minion

    echo $minion_id > /etc/salt/minion_id

    echo "Restarting the required services" | tee -a "${LOG_FILE}"
    systemctl start salt-master
    systemctl restart salt-minion
    echo "Done" | tee -a "${LOG_FILE}"

    echo "DEBUG: Waiting for key of $minion_id to become connected to salt-master" >> "${LOG_FILE}"
    try=1; max_tries=10
    until salt-key --list-all | grep "srvnode-0" >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: Key for salt-minion $minion_id not listed after $max_tries attemps." >> "${LOG_FILE}"
            echo "ERROR: Provisioner configuration manager failed for key acceptance" | tee -a "${LOG_FILE}"
            salt-key --list-all >&2
            exit 1
        fi
        try=$(( try + 1 ))
        sleep 5
    done
    echo "DEBUG: Key for $minion_id is listed." >> "${LOG_FILE}"
    echo "DEBUG: Accepting the salt key for minion $minion_id" >> "${LOG_FILE}"
    salt-key -y -a $minion_id $salt_opts

    # Check if salt '*' test.ping works
    echo "Waiting for Provisioner configuratoin manager to become ready" | tee -a "${LOG_FILE}"
    try=1; max_tries=10
    until salt -t 1 $minion_id test.ping >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: Minion $minion_id seems still not ready after $max_tries attempts." >> "${LOG_FILE}"
            echo "ERROR: Provisioner configuration manager failed to connect to local server" | tee -a "${LOG_FILE}"
            exit 1
        fi
        try=$(( try + 1 ))
    done
    echo "DEBUG: Salt configuration done successfully" >> "${LOG_FILE}"
    echo "Done" | tee -a "${LOG_FILE}"
}

setup_repos()
{
    repo=$1
    echo "Cleaning yum cache" | tee -a "${LOG_FILE}"
    yum clean all
    rm -rf /var/cache/yum/* || true
    echo "Configuring the repository: ${repo}/3rd_party" | tee -a "${LOG_FILE}"
    yum-config-manager --add-repo "${repo}/3rd_party/"
    echo "Configuring the repository: ${repo}/cortx_iso" | tee -a "${LOG_FILE}"
    yum-config-manager --add-repo "${repo}/cortx_iso/"

    echo "DEBUG: Preparing the pip.conf" >> "${LOG_FILE}"
    cat << EOL > /etc/pip.conf
[global]
timeout: 60
index-url: $repo_url/python_deps/
trusted-host: cortx-storage.colo.seagate.com
EOL
    echo "DEBUG: generated pip3 conf file" >> "${LOG_FILE}"
    cat /etc/pip.conf >> "${LOG_FILE}"

}

install_dependency_pkgs()
{
    echo "Installing dependency packages" | tee -a "${LOG_FILE}"
    dependency_pkgs=(
        "java-1.8.0-openjdk-headless"
        "python3 sshpass"
        "python36-m2crypto"
        "salt"
        "salt-master"
        "salt-minion"
    )
    for pkg in ${dependency_pkgs[@]}; do
        if rpm -qi --quiet $pkg; then
            echo "Package $pkg is already installed."
        else
            echo "Installing $pkg" | tee -a "${LOG_FILE}"
            yum install --nogpgcheck -y -q $pkg | tee -a "${LOG_FILE}"
        fi
    done

    if [[ -d "/opt/nodejs/node-v12.13.0-linux-x64" ]]; then
        echo "nodejs already installed" | tee -a "${LOG_FILE}"
    else
        echo "Installing nodejs" | tee -a "${LOG_FILE}"
        echo "DEBUG: Downloading nodeja tarball" >> "${LOG_FILE}"
        wget ${nodejs_tar}
        mkdir /opt/nodejs
        echo "DEBUG: Extracting the tarball" >> "${LOG_FILE}"
        tar -C /opt/nodejs/ -xf node-v12.13.0-linux-x64.tar.xz >> "${LOG_FILE}"
        echo "DEBUG: The extrracted tarball is kept at /opt/nodejs, removing the tarball ${nodejs_tar}" >> "${LOG_FILE}"
        rm -rf ${nodejs_tar}
        echo "Done" | tee -a "${LOG_FILE}"
    fi
}

install_cortx_pkgs()
{
    echo "Installing Cortx packages" | tee -a "${LOG_FILE}"
    cortx_pkgs=(
        "cortx-prereq"
        "python36-cortx-prvsnr"
        "cortx-prvsnr"
        "cortx-cli"
        "cortx-py-utils"
        "cortx-csm_agent"
        "cortx-csm_web"
        "cortx-ha"
        "cortx-hare"
        "cortx-libsspl_sec"
        "cortx-libsspl_sec-method_none"
        "cortx-libsspl_sec-method_pki"
        "cortx-motr"
        "cortx-motr-ivt"
        "cortx-prereq"
        "cortx-prvsnr-cli"
        "cortx-s3server"
        "cortx-sspl"
        "cortx-sspl-cli"
        "python36-cortx-prvsnr"
        "udx-discovery"
        "stats_utils"
    )

    for pkg in ${cortx_pkgs[@]}; do
        if rpm -qi --quiet $pkg; then
            echo "Package $pkg is already installed." | tee -a "${LOG_FILE}"
        else
            echo "Installing $pkg" | tee -a "${LOG_FILE}"
            yum install --nogpgcheck -y -q $pkg | tee -a "${LOG_FILE}"
        fi
    done

    if ! command -v cortx_setup; then
        ## WORKAROUND UNTIL EOS_21317 IS ADDRESSED.
        echo "Preparing the Cortx ConfStore with default configuration" | tee -a "${LOG_FILE}"
        echo "WARNING: python36-cortx-setup package is not installed" | tee -a "${LOG_FILE}"
        echo "Installing cortx_setup commands using pip" | tee -a "${LOG_FILE}"
        pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@pre-cortx-1.0#subdirectory=lr-cli/
        if ! command -v cortx_setup; then
            echo "DEBUG: Updating the path variable" >> "${LOG_FILE}"
            export PATH=${PATH}:/usr/local/bin/
            if ! command -v cortx_setup; then
                echo "ERROR: cortx_setup command still not available " | tee -a "${LOG_FILE}"
                echo "ERROR: Please check if cortx_setup commands"\
                " are installed at correct location and environment variable PATH is updated." | tee -a "${LOG_FILE}"
                exit 1
            fi
        fi
    fi
    if ! command -v provisioner; then
        echo "ERROR: Could not find the provisioner command" | tee -a "${LOG_FILE}"
        echo "ERROR: Ensure the appropriate package is installed and then try again" | tee -a "${LOG_FILE}"
        exit 1
    fi
    echo "Done" | tee -a "${LOG_FILE}"
}

download_isos()
{
    CORTX_RELEASE_REPO=$1
    echo "Downloading the ISOs" | tee -a "${LOG_FILE}"
    mkdir /opt/isos
    cortx_iso=$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's\/<\\/*[^>]*>\/\/g' | cut -f1 -d' ' | grep 'single.iso')
    curl -O ${CORTX_RELEASE_REPO}/iso/\${cortx_iso}
    os_iso=$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's\/<\\/*[^>]*>\/\/g' | cut -f1 -d' '|grep  "cortx-os")
    curl -O ${CORTX_RELEASE_REPO}/iso/\${os_iso}
    #CORTX_PREP=$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's\/<\\/*[^>]*>\/\/g' | cut -f1 -d' '|grep  ".sh")
    #curl -O ${CORTX_RELEASE_REPO}/iso/\${CORTX_PREP}
}

main()
{
    echo "DEBUG: Running Cortx-prep script" >> "${LOG_FILE}"
    parse_args $@
    #TODO: uncomment once ready
    #    create_factory_user $user_name $uid $group $gid
    if hostnamectl status | grep Chassis | grep -q server; then
        echo "DEBUG: This is Hardware" >> "${LOG_FILE}"
        if systemctl list-units | grep scsi-network-relay; then
            systemctl start scsi-network-relay
        else
            echo "ERROR scsi-network-relay service is not present" | tee -a "${LOG_FILE}"
            exit 1
        fi
        if [[ ! -z $repo_url ]]; then
            # User has provided target-build for HW
            # Remove the ISOs set up by Kickstart
            # download the iso from provided build url
            # mount the iso

            #echo "Removing the ISOs setup by Kickstart" | tee -a "${LOG_FILE}"
            #TODO:
                #remove_isos
                #download_isos $repo_url
                #mount_isos
                #configure repos from iso files

            #WORKAROUND: Use hosted repos until download_isos function is ready
            setup_repos $repo_url
        else
            echo "DEBUG: Using the ISO files set up by kickstart " >> "${LOG_FILE}"
            #TODO: use the same isos downloaded by KS file to install the packages
            # configure repos from iso files

            echo "ERROR: Please provide the target-build unless kickstart file is in place" | tee -a "${LOG_FILE}"
            exit 1
        fi
    else
        echo "This is VM" >> "${LOG_FILE}"
        if [[ ! -z $repo_url ]]; then
            setup_repos $repo_url
        else
            echo "ERROR: target-build not provided, it's mandetary option for VM"
            echo "ERROR: Please provide the target-build " | tee -a "${LOG_FILE}"
            exit 1
        fi
    fi

    install_dependency_pkgs
    install_cortx_pkgs
    config_local_salt
    echo "Resetting the machine id" | tee -a "${LOG_FILE}"
    salt-call state.apply components.provisioner.config.machine_id.reset $salt_opts
    echo "Done" | tee -a "${LOG_FILE}"
    echo "Preparing the Cortx ConfStore with default values" | tee -a "${LOG_FILE}"
    cortx_setup prepare_confstore
    echo "Done" | tee -a "${LOG_FILE}"
}

main $@
echo "Cortx prep script run successfully" | tee -a "${LOG_FILE}"
