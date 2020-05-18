#!/bin/bash

set -euE

LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/cortx-prereqs.log}"
export LOG_FILE

function trap_handler {
  echo "***** FAILED!! *****"
  echo "For more details see $LOG_FILE"
  exit 2
}

function trap_handler_exit {
  if [[ $? -eq 1 ]]; then
      echo "***** FAILED!! *****"
      echo "For more details see $LOG_FILE"
  else
      exit $?
  fi
}

trap trap_handler ERR
trap trap_handler_exit EXIT

if [[ ! -e "$LOG_FILE" ]]; then
    mkdir -p $(dirname "${LOG_FILE}")
fi

do_reboot=false
disable_sub_mgr_opt=false

usage()
{
    echo "\

    Cortx Prerequisite script.

    Usage:
         $0 [--disable-sub-mgr] [-h|--help]

    OPTION:
    --disable-sub-mgr     For RHEL. To install prerequisites by disabling
                          subscription manager (usually, not recommended).
                          If this option is not provided it is expected that
                          either the system is not RHEL or system is already
                          registered with subscription manager.
    "
    exit 0
}

parse_args()
{
    if [[ "$#" -gt 0 ]]; then
        case "$1" in
        --disable-sub-mgr)
            disable_sub_mgr_opt=true
        ;;
        -h|--help)
            usage
        ;;
        *)
            echo -e "\nERROR: Unknown option provided: $1"
            exit 1
        esac
    fi
}

create_commons_repo_rhel()
{
    _repo="/etc/yum.repos.d/cortx_platform_commons_rhel.repo"
    echo "INFO: Creating $_repo" 2>&1 | tee -a ${LOG_FILE}
    _url="$1"
cat <<EOF > ${_repo}
[cortx-platform-commons-rhel]
name=cortx-platform-commons-rhel
gpgcheck=0
enabled=1
baseurl=$_url
EOF

echo "INFO: Created $_repo"
}

create_commons_repos()
{
    _repo="/etc/yum.repos.d/cortx_platform_commons.repo"
    echo "INFO: Creating $_repo" 2>&1 | tee -a ${LOG_FILE}
    _url="$1"
cat <<EOF > ${_repo}
[cortx-platform-commons]
name=lyve-platform-commons
gpgcheck=0
enabled=1
baseurl=$_url

[cortx-platform-base]
name=lyve-platform-base
gpgcheck=0
enabled=1
baseurl=http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/CentOS-7/CentOS-7-OS/

[cortx-platform-epel]
name=lyve-platform-epel
gpgcheck=0
enabled=1
baseurl=http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/EPEL-7/EPEL-7/

[cortx-platform-extras]
name=lyve-platform-extras
gpgcheck=0
enabled=1
baseurl=http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/CentOS-7/CentOS-7-Extras/

EOF

    echo "INFO: Created $_repo"
}

parse_args "$@"

echo "***** Running $0 *****" 2>&1 | tee -a ${LOG_FILE}

echo "INFO: Checking If the hostnames are ok" 2>&1 | tee -a ${LOG_FILE}
srvnode_hostname=`hostname -f`
if [[ $srvnode_hostname != *"."* ]]; then
      echo -e "\nERROR: 'hostname -f' did not return the FQDN, please set FQDN and retry." 2>&1 | tee -a ${LOG_FILE}
      exit 1
fi

echo "INFO: hostname is OK: $srvnode_hostname" 2>&1 | tee -a ${LOG_FILE}

echo "INFO: Checking if kernel version is correct" 2>&1 | tee -a ${LOG_FILE}
kernel_version=`uname -r`
if [[ "$kernel_version" != '3.10.0-1062.el7.x86_64' ]]; then
    echo "ERROR: Kernel version is wrong. Required: 3.10.0-1062.el7.x86_64, installed: $kernel_version" 2>&1 | tee -a ${LOG_FILE}
    exit 1
fi

if [[ "$disable_sub_mgr_opt" == true ]]; then
    grep -q "Red Hat" /etc/*-release && {
        echo "INFO: disabling the Red Hat Subscription Manager" 2>&1 | tee -a ${LOG_FILE}
        subscription-manager auto-attach --disable || true
        subscription-manager remove --all || true
        subscription-manager unregister || true
        subscription-manager clean || true
        subscription-manager config --rhsm.manage_repos=0
        echo "INFO: Creating repos for Cotrx" 2>&1 | tee -a ${LOG_FILE}
        create_commons_repos "http://ci-storage.mero.colo.seagate.com/releases/eos/uploads_rhel/"
        echo "INFO: Cleaning yum cache" 2>&1 | tee -a ${LOG_FILE}
    } || {
        echo "ERROR: This is not RedHat system, ignoring --disable-sub-mgr option"
        echo "INFO: Creating repos for Cotrx" 2>&1 | tee -a ${LOG_FILE}
        create_commons_repos "http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/"
        echo "INFO: Cleaning yum cache" 2>&1 | tee -a ${LOG_FILE}
    }
else
    grep -q "Red Hat" /etc/*-release && { 
        echo "INFO: Checking if RHEL subscription manager is enabled" 2>&1 | tee -a ${LOG_FILE}
        subc_list=`subscription-manager list | grep Status: | awk '{ print $2 }'`
        subc_status=`subscription-manager status | grep "Overall Status:" | awk '{ print $3 }'`

        if [[ "$subc_list" = "Subscribed" && "$subc_status" = "Current" ]]; then
            # Ensure required repos are enabled in subscription
            echo "INFO: subscription-manager is enabled." 2>&1 | tee -a ${LOG_FILE}
            repos_list=(
                "rhel-7-server-optional-rpms"
                "rhel-7-server-satellite-tools-6.6-rpms"
                "rhel-7-server-rpms"
                "rhel-7-server-extras-rpms"
                "rhel-7-server-supplementary-rpms"
                "rhel-ha-for-rhel-7-server-rpms"
            )
            subscription-manager config --rhsm.manage_repos=1
            echo "INFO: Checking if required repos are enabled." 2>&1 | tee -a ${LOG_FILE}
            for repo in ${repos_list[@]}
            do
                subscription-manager repos --list-enabled | grep ID | grep -q $repo && {
                    echo -e "\trepo $repo is enabled" 2>&1 | tee -a ${LOG_FILE}
                } || {
                    echo "ERROR: repo $repo is not enabled, checking if it's available" >> tee -a ${LOG_FILE}
                    subscription-manager repos --list | grep ID | grep $repo && {
                        echo "INFO: Enabling repo $repo...... " 2>&1 | tee -a ${LOG_FILE}
                        subscription-manager repos --enable $repo  2>&1 | tee -a ${LOG_FILE}
                        subscription-manager repos --list | grep ID | grep -q $repo && {
                            echo -ne "Done" 2>&1 | tee -a ${LOG_FILE}
                        } || {
                            echo -e "\n\nERROR: Repo $repo is not available, exiting..." 2>&1 | tee -a ${LOG_FILE}
                            exit 1
                        }
                    }
                }
            done
            _bkpdir=/etc/yum.repos.d.bkp
            echo "INFO: Taking backup of /etc/yum.repos.d/*.repo to ${_bkpdir}"
            mkdir -p ${_bkpdir}
            yes | cp -rf /etc/yum.repos.d/*.repo ${_bkpdir}
            find /etc/yum.repos.d/ -type f ! -name 'redhat.repo' -delete

            #Set repo for Mellanox drivers
            echo "INFO: Checking if Mellanox repository from Satellite subscription is enabled" 2>&1 | tee -a ${LOG_FILE}
            subscription-manager --list-enabled repos | grep ID: | grep -q EOS_Mellanox && {
                echo "INFO: Disabling Mellanox repository from Satellite subscription" 2>&1 | tee -a ${LOG_FILE}
                subscription-manager repos --disable=EOS_Mellanox*
            }
            echo "INFO: Enabling epel repository" 2>&1 | tee -a ${LOG_FILE}
            subscription-manager --list-enabled repos | grep ID: | grep -q EOS_EPEL && {
                echo "INFO: EOS_EPEL repository is enabled from Satellite subscription" 2>&1 | tee -a ${LOG_FILE}
                #subscription-manager repos --disable=EOS_EPEL*
            } || {
                echo "INFO: Installing the Public Epel repository" 2>&1 | tee -a ${LOG_FILE}
                yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm 2>&1 | tee -a ${LOG_FILE}
            }

            # Create commons repo for installing mellanox drivers
            create_commons_repo_rhel "http://ci-storage.mero.colo.seagate.com/releases/eos/uploads_rhel/"

            #echo "INFO: Installing yum-plugin-versionlock" 2>&1 | tee ${LOG_FILE}
            #yum install -y yum-plugin-versionlock
            #echo "INFO: Restricting the kernel updates to current kernel version" 2>&1 | tee -a ${LOG_FILE}
            #yum versionlock kernel-3.10.0-1062.el7.x86_64
        else
            echo -e "\nERROR: RedHat subscription manager is disabled." 2>&1 | tee -a ${LOG_FILE}
            echo "       Please register the system with Subscription Manager and rerun the command." 2>&1 | tee -a ${LOG_FILE}
            exit 1
        fi
    } || {
        echo -e "\nThis is not a RedHat system, copying repos manually" 2>&1 | tee -a ${LOG_FILE}
        echo "INFO: Creating repos for Cotrx" 2>&1 | tee -a ${LOG_FILE}
        create_commons_repos "http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/"
    }
fi

echo "INFO: Cleaning yum cache" 2>&1 | tee -a ${LOG_FILE}
yum clean all

hostnamectl status | grep Chassis | grep -q server && {
    rpm -qa | grep -q mlnx-ofed-all && rpm -qa | grep -q mlnx-fw-updater && {
        echo "INFO: Mellanox Drivers are already installed." 2>&1 | tee -a ${LOG_FILE}
    } || {
        echo "INFO: Installing Mellanox drivers" 2>&1 | tee -a ${LOG_FILE}
        yum install -y mlnx-ofed-all mlnx-fw-updater
        echo "INFO: Rebooting the system now" 2>&1 | tee -a ${LOG_FILE}
        do_reboot=true
    }
    echo "INFO: Installing sg3_utils" 2>&1 | tee -a ${LOG_FILE}
    yum install -y sg3_utils 2>&1 | tee -a ${LOG_FILE}
    echo "INFO: Scanning SCSI bus" >> ${LOG_FILE}
    /usr/bin/rescan-scsi-bus.sh -a 2>&1 | tee -a ${LOG_FILE}
}

echo "***** SUCCESS!!! *****" 2>&1 | tee -a ${LOG_FILE}
echo "For more details see: $LOG_FILE"
if [[ "$do_reboot" == true ]]; then
    echo "INFO: Rebooting the system now" 2>&1 | tee -a ${LOG_FILE}
    shutdown -r now
fi

