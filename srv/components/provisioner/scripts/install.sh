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
repo_url=
nodejs_tar=
use_local_repo=false

function trap_handler {
    exit_code=$?
    if [[ ${exit_code} != 0 && ${exit_code} != 2 ]]; then
      echo "***** ERROR! *****"
      echo "For detailed error logs, please see: $LOG_FILE"
      echo "******************"
      exit $exit_code
    fi
}
trap trap_handler ERR

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
    echo "DEBUG: parse_args(): parsing input arguments" >> "${LOG_FILE}"
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--target-build)
                set +u
                if [[ -z "$2" ]]; then
                    echo "Error: URL for target cortx build not provided"
                    _usage
                    exit 2
                fi
                set -u
                repo_url="$2"
                shift 2
                if echo "${repo_url}" | grep -q file; then
                    # local iso path
                    use_local_repo=true
                    iso_mount_path=$(echo "${repo_url}" | cut -d: -f 2 | sed 's/^..//')
                    if [[ ! -d "${iso_mount_path}" ]]; then
                        echo "ERROR: Invalid URL provided: $repo_url" | tee -a "${LOG_FILE}"
                        exit 1
                    fi
                    # Validate the directory structure of the mount path
                    # Validation for cortx iso
                    if [[ ! -f "${iso_mount_path}/components/3rd_party/repodata/repomd.xml" ]]; then
                        echo "ERROR: Invalid Cortx ISO provided" | tee -a "${LOG_FILE}" | tee -a "${LOG_FILE}"
                        echo "ERROR: Could not find ${iso_mount_path}/components/3rd_party/repodata/repomd.xml" | tee -a "${LOG_FILE}"
                        echo "ERROR: Please ensure the Cortx ISO is mounted at /mnt/cortx/components" | tee -a "${LOG_FILE}"
                        exit 1
                    fi
                    if [[ ! -f "${iso_mount_path}/components/cortx_iso/repodata/repomd.xml" ]]; then
                        echo "ERROR: Invalid Cortx ISO provided" | tee -a "${LOG_FILE}" | tee -a "${LOG_FILE}"
                        echo "ERROR: Could not find ${iso_mount_path}/components/cortx_iso/repodata/repomd.xml" | tee -a "${LOG_FILE}"
                        echo "ERROR: Please ensure the Cortx ISO is mounted at /mnt/cortx/components" | tee -a "${LOG_FILE}"
                        exit 1
                    fi
                    if [[ ! -f "${iso_mount_path}/components/python_deps/index.html" ]]; then
                        echo "ERROR: Invalid Cortx ISO provided" | tee -a "${LOG_FILE}" | tee -a "${LOG_FILE}"
                        echo "ERROR: Could not find ${iso_mount_path}/components/python_deps/index.html" | tee -a "${LOG_FILE}"
                        echo "ERROR: Please ensure the Cortx ISO is mounted at /mnt/cortx/components" | tee -a "${LOG_FILE}"
                        exit 1
                    fi

                    # Validation for os iso
                    if [[ ! -f "${iso_mount_path}/dependencies/repodata/repomd.xml" ]]; then
                        echo "ERROR: Invalid Cortx-OS ISO provided" | tee -a "${LOG_FILE}" | tee -a "${LOG_FILE}"
                        echo "ERROR: Could not find ${iso_mount_path}/dependencies/repodata/repomd.xml" | tee -a "${LOG_FILE}"
                        echo "ERROR: Please ensure the Cortx-OS ISO is mounted at /mnt/cortx/dependencies" | tee -a "${LOG_FILE}"
                        exit 1
                    fi

                else
                    #hosted repo, validate the url
                    repo_url_3rd_party="${repo_url}/3rd_party/repodata/repomd.xml"
                    repo_url_cortx_iso="${repo_url}/cortx_iso/repodata/repomd.xml"
                    repo_url_python_deps="${repo_url}/python_deps"
                    for url in "${repo_url_3rd_party}" "${repo_url_cortx_iso}" "${repo_url_python_deps}"; do
                        connect_status=$(curl -o /dev/null --silent --head --write-out '%{http_code}' "$url")
                        if [[ "$connect_status" == 404 ]]; then
                            echo "ERROR: Failed to connect to $url" | tee -a "${LOG_FILE}"
                            echo "ERROR: Target URL provided is either unreachable or it doesn't point to the valid Cortx build" | tee -a "${LOG_FILE}"
                            exit 1
                        else
                            echo "DEBUG: Valid url: $url" >> "${LOG_FILE}"
                        fi
                    done
                fi
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

    echo "Starting provisioner environment configuration" | tee -a "${LOG_FILE}"
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
    sleep 10
    status=$(systemctl status salt-minion | grep Active | awk '{ print $2 }')
    if [[ "$status" != "active" ]]; then
        echo "Salt minion service failed to start" >> "${LOG_FILE}"
        echo "Could not start the required services to set up the environment" | tee -a "${LOG_FILE}"
        exit 1
    fi
    echo "Done" | tee -a "${LOG_FILE}"
    echo "Verifying the configuraion" | tee -a "${LOG_FILE}"
    echo "DEBUG: Waiting for key of $minion_id to become connected to salt-master" >> "${LOG_FILE}"
    try=1; max_tries=10
    until salt-key --list-all | grep "srvnode-0" >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: Key for salt-minion $minion_id not listed after $max_tries attemps." >> "${LOG_FILE}"
            echo "ERROR: Cortx provisioner environment configuration failed" | tee -a "${LOG_FILE}"
            salt-key --list-all >&2
            exit 1
        fi
        try=$(( try + 1 ))
        sleep 5
    done
    echo "DEBUG: Key for $minion_id is listed." >> "${LOG_FILE}"
    echo "DEBUG: Accepting the salt key for minion $minion_id" >> "${LOG_FILE}"
    salt-key -y -a "$minion_id" --no-color --out-file="${LOG_FILE}" --out-file-append

    # Check if salt '*' test.ping works
    echo "Testing if the environment is working fine" | tee -a "${LOG_FILE}"
    try=1; max_tries=10
    until salt -t 1 "$minion_id" test.ping >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: Minion $minion_id seems still not ready after $max_tries attempts." >> "${LOG_FILE}"
            echo "ERROR: Cortx provisioner environment configuration failed" | tee -a "${LOG_FILE}"
            exit 1
        fi
        try=$(( try + 1 ))
    done
    echo "DEBUG: Salt configuration done successfully" >> "${LOG_FILE}"
    echo "Cortx provisioner environment configured successfully" | tee -a "${LOG_FILE}"
    echo "Done" | tee -a "${LOG_FILE}"
}

setup_repos_hosted()
{
    repo=$1
    for file in `grep -lE "cortx-storage.colo.seagate.com|file://" /etc/yum.repos.d/*.repo`; do
        echo "DEBUG: Removing old repo file: $file" >> "${LOG_FILE}"
        rm -f "$file"
    done

    echo "Configuring the repository: ${repo}/3rd_party" | tee -a "${LOG_FILE}"
    yum-config-manager --add-repo "${repo}/3rd_party/" >> "${LOG_FILE}"
    echo "Configuring the repository: ${repo}/cortx_iso" | tee -a "${LOG_FILE}"
    yum-config-manager --add-repo "${repo}/cortx_iso/" >> "${LOG_FILE}"

    echo "Cleaning yum cache" | tee -a "${LOG_FILE}"
    yum clean all || true >> "${LOG_FILE}"
    rm -rf /var/cache/yum/* || true

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

setup_repos_iso()
{
    mntpt="$1"
    cortx_iso_mntdir="${mntpt}/components"
    cortx_os_iso_mntdir="${mntpt}/dependencies"
    echo "DEBUG: Backing up exisitng repositories" >> "${LOG_FILE}"
    time_stamp=$(date "+%Y.%m.%d-%H.%M.%S")
    mv /etc/yum.repos.d /etc/yum.repos.d.${time_stamp} || true
    echo "INFO: Creating cortx_iso.repo" 2>&1 | tee -a ${LOG_FILE}
    mkdir -p /etc/yum.repos.d
    for repo in 3rd_party cortx_iso
    do
cat >> /etc/yum.repos.d/cortx_iso.repo <<EOF
[$repo]
baseurl=${cortx_iso_mntdir}/${repo}
gpgcheck=0
name=Repository ${repo}
enabled=1

EOF
    done

    echo "INFO: Creating cortx_os.repo" 2>&1 | tee -a ${LOG_FILE}
    touch /etc/yum.repos.d/cortx_os.repo
cat >> /etc/yum.repos.d/cortx_os.repo <<EOF
[Base]
baseurl=${cortx_os_iso_mntdir}
gpgcheck=0
name=Repository Base
enabled=1
EOF

    mv -f /etc/pip.conf /etc/pip.conf.bkp || true
    touch /etc/pip.conf
cat <<EOF >/etc/pip.conf
[global]
timeout: 60
index-url: ${cortx_iso_mntdir}/python_deps/
EOF

    echo "Done" 2>&1 | tee -a ${LOG_FILE}
    yum clean all || true
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
        "glusterfs-server"
        "glusterfs-client"
    )
    for pkg in ${dependency_pkgs[@]}; do
        if rpm -qi --quiet "$pkg"; then
            echo -e "\tPackage $pkg is already installed."
        else
            echo -e "\tInstalling $pkg" | tee -a "${LOG_FILE}"
            yum install --nogpgcheck -y -q "$pkg" >> "${LOG_FILE}" 2>&1
        fi
    done

    echo -e "\tInstalling nodejs" | tee -a "${LOG_FILE}"
    if [[ -d "/opt/nodejs/node-v12.13.0-linux-x64" ]]; then
        echo "nodejs already installed" | tee -a "${LOG_FILE}"
        return
    fi
    mkdir /opt/nodejs
    if [[ $use_local_repo == "true" ]]; then
        #local iso
        nodejs_tar="${repo_url}/components/3rd_party/commons/node/node-v12.13.0-linux-x64.tar.xz"
        echo -e "\tDEBUG: Extracting the tarball: ${nodejs_tar}" >> "${LOG_FILE}"
        tar -C /opt/nodejs/ -xf "${nodejs_tar}" >> "${LOG_FILE}"q
        echo -e "\tDEBUG: The extracted tarball is kept at /opt/nodejs" >> "${LOG_FILE}"
    else
        #hosted repo
        nodejs_tar="${repo_url}/3rd_party/commons/node/node-v12.13.0-linux-x64.tar.xz"
        echo -e "\tDEBUG: Downloading nodejs tarball: ${nodejs_tar}" >> "${LOG_FILE}"
        wget -P /opt/nodejs "${nodejs_tar}" >> "${LOG_FILE}" 2>&1
        echo -e "\tDEBUG: Extracting the tarball" >> "${LOG_FILE}"
        tar -C /opt/nodejs/ -xf "${nodejs_tar}" >> "${LOG_FILE}"
        echo -e "\tDEBUG: The extracted tarball is kept at /opt/nodejs, removing the tarball" >> "${LOG_FILE}"
        rm -rf "${nodejs_tar}"
    fi
    echo -e "\tInstalled all dependency packages successfully" | tee -a "${LOG_FILE}"
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
        "uds-pyi"
        "cortx-s3server"
        "cortx-sspl"
        "cortx-sspl-cli"
        "udx-discovery"
        "stats_utils"
        "python36-cortx-setup"
        "cortx-node-cli"
    )

    for pkg in ${cortx_pkgs[@]}; do
        if rpm -qi --quiet "$pkg"; then
            echo -e "\tPackage $pkg is already installed." | tee -a "${LOG_FILE}"
        else
            echo -e "\tInstalling $pkg" | tee -a "${LOG_FILE}"
            yum install --nogpgcheck -y -q "$pkg" 2>&1 >> "${LOG_FILE}"
        fi
    done

    echo "Installed all Cortx packages successfully" | tee -a "${LOG_FILE}"
}

setup_bash_env()
{
    if [[ "$use_local_repo" == false ]]; then 
        if grep -wq CORTX_RELEASE_REPO /root/.bashrc; then
            line_to_replace=$(grep -m1 -noP "CORTX_RELEASE_REPO" /root/.bashrc | tail -1 | cut -d: -f1)
            echo "DEBUG: line_to_replace: $line_to_replace" >> "${LOG_FILE}"
            sed -i "${line_to_replace}s|CORTX_RELEASE_REPO.*|CORTX_RELEASE_REPO=$repo_url|" /root/.bashrc
        else
            echo "CORTX_RELEASE_REPO=$repo_url" >> /root/.bashrc
        fi
        # Also update /etc/.bashrc so as to have the same environment variable set for new users created
        if grep -wq CORTX_RELEASE_REPO /etc/.bashrc; then
            line_to_replace=$(grep -m1 -noP "CORTX_RELEASE_REPO" /etc/.bashrc | tail -1 | cut -d: -f1)
            echo "DEBUG: line_to_replace: $line_to_replace" >> "${LOG_FILE}"
            sed -i "${line_to_replace}s|CORTX_RELEASE_REPO.*|CORTX_RELEASE_REPO=$repo_url|" /etc/.bashrc
        else
            echo "export CORTX_RELEASE_REPO=$repo_url" >> /etc/.bashrc
        fi
        export CORTX_RELEASE_REPO="$repo_url"
    fi
}

main()
{
    time_stamp=$(date)
    echo "DEBUG: run time: $time_stamp" >> "${LOG_FILE}"
    parse_args $@
    echo "*********************************************************" | tee -a "${LOG_FILE}"
    echo "      Setting up the factory environment for Cortx       " | tee -a "${LOG_FILE}"
    echo "*********************************************************" | tee -a "${LOG_FILE}"
    if hostnamectl status | grep Chassis | grep -q server; then
        echo "DEBUG: This is Hardware" >> "${LOG_FILE}"

        echo "Starting the scsi-network-relay service" | tee -a "${LOG_FILE}"
        try=0
        max_tries=30
        until systemctl list-units | grep scsi-network-relay; >/dev/null 2>&1
        do
            if [[ "$try" -gt "$max_tries" ]]; then
                echo "ERROR: scsi-network-relay is not available" | tee -a "${LOG_FILE}"
                echo "ERROR: Please install the appropriate package and try again" | tee -a "${LOG_FILE}"
                exit 1
            fi
            try=$(( try + 1 ))
            sleep 1
        done
        systemctl restart scsi-network-relay

#            setup_repos "$repo_url"
    fi
    if [[ "${use_local_repo}" == true ]]; then
        setup_repos_iso "$repo_url"
    else
        setup_repos_hosted "$repo_url"
    fi

    install_dependency_pkgs
    install_cortx_pkgs
    config_local_salt
    echo "Resetting the machine id" | tee -a "${LOG_FILE}"
    salt-call state.apply components.provisioner.config.machine_id.reset --no-color --out-file="${LOG_FILE}" --out-file-append
    echo "Done" | tee -a "${LOG_FILE}"
    echo "Preparing the Cortx ConfStore with default values" | tee -a "${LOG_FILE}"
    cortx_setup prepare_confstore
    echo "Setting up the shell environment" | tee -a "${LOG_FILE}"
    setup_bash_env
    echo "Done" | tee -a "${LOG_FILE}"
}

main $@
echo "\
************************* SUCCESS!!! **************************************

Successfully set up the factory environment for Cortx !!

The detailed logs are available at: $LOG_FILE
***************************************************************************" | tee -a "${LOG_FILE}"
