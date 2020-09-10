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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#


set -eE

LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/cortx-prereqs.log}"
export LOG_FILE

tmpdir="/tmp/_cortx_prereqs_"
mkdir -p $tmpdir

tgt_build=
cortx_deps_repo=
saltstack_repo=
epel_repo=
bundled_release=false

# Repo url for in house built commons packages Non RHEL systems
url_local_repo_commons="http://cortx-storage.colo.seagate.com/releases/eos/uploads/centos/centos-7.7.1908/"

# Repo url for in house built commons packages for RHEL systems
url_local_repo_commons_rhel="http://cortx-storage.colo.seagate.com/releases/eos/uploads/rhel/rhel-7.7.1908/"

# Repo url for in house built HA packages for RHEL systems
#url_local_repo_rhel_ha="http://cortx-storage.colo.seagate.com/releases/eos/rhel_local_ha/"

# Repo url for Saltstack
# url_saltstack_repo="https://repo.saltstack.com/py3/redhat/$releasever/$basearch/3000"

function trap_handler {
    rm -rf $tmpdir || true
    echo "***** FAILED!! *****"
    echo "For more details see $LOG_FILE"
    exit 2
}

function trap_handler_exit {
    rm -rf $tmpdir || true
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
         $0 [-t <target build url>] [--disable-sub-mgr] [-h|--help]

    OPTION:
    --disable-sub-mgr     For RHEL. To install prerequisites by disabling
                          subscription manager (usually, not recommended).
                          If this option is not provided it is expected that
                          either the system is not RHEL or system is already
                          registered with subscription manager.
    -t                    target build url pointed to release bundle base directory,
                          if specified the following directory structure is assumed:
                          <base_url>/
                               rhel7.7 or centos7.7   <- OS ISO is mounted here
                               3rd_party              <- CORTX 3rd party ISO is mounted here
                               cortx_iso              <- CORTX ISO (main) is mounted here
    "
    exit 0
}

parse_args()
{
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --disable-sub-mgr)
            disable_sub_mgr_opt=true
            shift
        ;;
        -h|--help)
            usage
        ;;
        -t)
            [ -z "$2" ] &&
                echo "Error: Target build not provided" && exit 1;
            tgt_build="$2"

            bundled_release=true

            grep -q "Red Hat" /etc/*-release && {
                subc_list=`subscription-manager list | grep Status: | awk '{ print $2 }'`
                subc_status=`subscription-manager status | grep "Overall Status:" | awk '{ print $3 }'`
                if echo "$subc_list" | grep -q "Subscribed" && "$subc_status" == "Current"; then
                    system_repo="${tgt_build}/rhel7.7"
                else
                    system_repo="${tgt_build}/centos7.7"
                fi
            } || {
                system_repo="${tgt_build}/centos7.7"
            }

            #grep -q "Red Hat" /etc/*-release && {
            #    system_repo="${tgt_build}/rhel7.7"
                # l_info "OS RHEL: Use subscription manager with appropriate subscriptions mentioned in Seagate setup docs to enable required package repositories."
            #} || {
            #    system_repo="${tgt_build}/centos7.7"
            #}

            cortx_deps_repo="${tgt_build}/3rd_party"
            epel_repo="${cortx_deps_repo}/EPEL-7"

            url_saltstack_repo="${cortx_deps_repo}/commons/saltstack-3001"
            url_local_repo_commons_rhel="$cortx_deps_repo"
            url_local_repo_commons="$cortx_deps_repo"

            shift 2 ;;
        *)
            echo -e "\nERROR: Unknown option provided: $1"
            exit 1
        esac
    done
}

create_commons_repo_rhel()
{
    _repo_name="$1"
    _url="$2"
    _repo="/etc/yum.repos.d/${_repo_name}.repo"
    echo -ne "\tCreating ${_repo}.................." 2>&1 | tee -a ${LOG_FILE}

cat <<EOF > ${_repo}
[$_repo_name]
name=$_repo_name
gpgcheck=0
enabled=1
baseurl=$_url
EOF
    echo "Done." 2>&1 | tee -a ${LOG_FILE}

}

create_commons_repos()
{
    cortx_commons_url="${1:-$url_local_repo_commons}"
    local _repo="/etc/yum.repos.d/cortx_commons.repo"
    local _url="$cortx_commons_url"
    echo -ne "\tCreating ${_repo}................." 2>&1 | tee -a ${LOG_FILE}
cat <<EOL > ${_repo}
[cortx_commons]
name=cortx_commons
gpgcheck=0
enabled=1
baseurl=$_url
EOL
    echo "Done" | tee -a ${LOG_FILE}

    _repo="/etc/yum.repos.d/cortx_platform_base.repo"
    if [[ "$bundled_release" == true && -z $LAB_ENV ]]; then
        _url="${system_repo}/os/"
    else
        _url="http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/CentOS-7/CentOS-7-OS/"
    fi
    echo -ne "\tCreating ${_repo}..........." 2>&1 | tee -a ${LOG_FILE}
cat <<EOL > ${_repo}
[cortx_platform_base]
name=cortx_platform_base
gpgcheck=0
enabled=1
baseurl=$_url
EOL
    echo "Done" | tee -a ${LOG_FILE}

    _repo="/etc/yum.repos.d/cortx_platform_extras.repo"
    if [[ "$bundled_release" == true && -z $LAB_ENV ]]; then
        _url="${system_repo}/extras/";    # FIXME EOS-12508
    else
        _url="http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/CentOS-7/CentOS-7-Extras/"
    fi
    echo -ne "\tCreating ${_repo}........." 2>&1 | tee -a ${LOG_FILE}
cat <<EOL > ${_repo}
[cortx_platform_extras]
name=cortx_platform_extras
gpgcheck=0
enabled=1
baseurl=$_url
EOL
    echo "Done" | tee -a ${LOG_FILE}

    _repo="/etc/yum.repos.d/3rd_party_epel.repo"
    if [[ "$bundled_release" == true ]]; then
        _url="$epel_repo"
    else
        _url="http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/EPEL-7/EPEL-7/"
    fi
    echo -ne "\tCreating ${_repo}.........................." 2>&1 | tee -a ${LOG_FILE}
cat <<EOL > ${_repo}
[epel]
name=epel
gpgcheck=0
enabled=1
baseurl=$_url
EOL

    echo "Done." 2>&1 | tee -a ${LOG_FILE}
}

parse_args "$@"

echo "***** Running $0 *****" 2>&1 | tee -a ${LOG_FILE}

echo -n "INFO: Checking hostnames............................................." 2>&1 | tee -a ${LOG_FILE}

srvnode_hostname=`hostname -f`
if [[ $srvnode_hostname != *"."* ]]; then
    echo -e "\nERROR: 'hostname -f' did not return the FQDN, please set FQDN and retry." 2>&1 | tee -a ${LOG_FILE}
    exit 1
else
    echo "Done." 2>&1 | tee -a ${LOG_FILE}
fi

echo -n "INFO: Checking if kernel version is correct.........................." 2>&1 | tee -a ${LOG_FILE}

kernel_version=`uname -r`
if [[ "$kernel_version" != '3.10.0-1062.el7.x86_64' ]]; then
    echo "ERROR: Kernel version is wrong. Required: 3.10.0-1062.el7.x86_64, installed: $kernel_version" 2>&1 | tee -a ${LOG_FILE}
    exit 1
else
    echo "Done." 2>&1 | tee -a ${LOG_FILE}
fi

if [[ "$disable_sub_mgr_opt" == true ]]; then
    grep -q "Red Hat" /etc/*-release && {
        echo -n "INFO: disabling the Red Hat Subscription Manager....................." 2>&1 | tee -a ${LOG_FILE}

        subscription-manager auto-attach --disable || true
        subscription-manager remove --all || true
        subscription-manager unregister || true
        subscription-manager clean || true
        subscription-manager config --rhsm.manage_repos=0
        puppet agent --disable "Cortx Stack Deploy Automation"
        echo "Done." 2>&1 | tee -a ${LOG_FILE} && sleep 1
        echo "INFO: Creating repos for Cotrx" 2>&1 | tee -a ${LOG_FILE}
        create_commons_repos "$url_local_repo_commons_rhel"
    } || {
        echo "ERROR: This is not RedHat system, ignoring --disable-sub-mgr option"
        echo "INFO: Creating repos for Cotrx" 2>&1 | tee -a ${LOG_FILE}
        create_commons_repos "$url_local_repo_commons"
    }

else
    grep -q "Red Hat" /etc/*-release && {
        # FIXME EOS-12508 do we need an iso for rhel7.7 if subscription is kept enabled
        echo "INFO: Checking if RHEL subscription manager is enabled" 2>&1 | tee -a ${LOG_FILE}
        subc_list=`subscription-manager list | grep Status: | awk '{ print $2 }'`
        subc_status=`subscription-manager status | grep "Overall Status:" | awk '{ print $3 }'`
        if echo "$subc_list" | grep -q "Subscribed"; then
            if [[  "$subc_status" != "Current" ]]; then
                echo -e "\nERROR: RedHat subscription manager is disabled." 2>&1 | tee -a ${LOG_FILE}
                echo "       Please register the system with Subscription Manager and rerun the command." 2>&1 | tee -a ${LOG_FILE}
                exit 1
            fi
            # Ensure required repos are enabled in subscription
            echo "INFO: subscription-manager is enabled." 2>&1 | tee -a ${LOG_FILE}
            repos_list=(
                "rhel-7-server-optional-rpms"
                "rhel-7-server-satellite-tools-6.7-rpms"
                "rhel-7-server-rpms"
                "rhel-7-server-extras-rpms"
                "rhel-7-server-supplementary-rpms"
            )
            subscription-manager config --rhsm.manage_repos=1
            echo "INFO: Checking available repos through subscription" 2>&1 | tee -a ${LOG_FILE}
            echo -ne "\t This might take some time..................................." | tee -a ${LOG_FILE}

            repos_all="${tmpdir}/repos.all"
            repos_enabled="${tmpdir}/repos.enabled"
            subscription-manager repos --list > ${repos_all}
            subscription-manager repos --list-enabled > ${repos_enabled}
            echo "Done." 2>&1 | tee -a ${LOG_FILE} && sleep 1
            echo "INFO: Checking if required repos are enabled." 2>&1 | tee -a ${LOG_FILE}
            for repo in ${repos_list[@]}
            do
                cat ${repos_enabled} | grep ID | grep -q $repo && {
                    echo -e "\trepo:$repo......enabled." 2>&1 | tee -a ${LOG_FILE}
                } || {
                    echo -e "\trepo:$repo......not enabled, checking if it's available" 2>&1 | tee -a ${LOG_FILE}
                    cat ${repos_all} | grep ID | grep -q $repo && {
                        echo -ne "\tRepo:$repo is available, enabling it......" 2>&1 | tee -a ${LOG_FILE}
                        subscription-manager repos --enable $repo  >> ${LOG_FILE}
                        echo "Done." 2>&1 | tee -a ${LOG_FILE} && sleep 1
                    } || {
                        echo -e "\n\nERROR: Repo $repo is not available, exiting..." 2>&1 | tee -a ${LOG_FILE}
                        exit 1
                    }
                }
            done
            _bkpdir=/etc/yum.repos.d.bkp
            echo "INFO: Taking backup of /etc/yum.repos.d/*.repo to ${_bkpdir}"
            mkdir -p ${_bkpdir}
            yes | cp -rf /etc/yum.repos.d/*.repo ${_bkpdir}
            find /etc/yum.repos.d/ -type f ! -name 'redhat.repo' -delete

            #Set repo for Mellanox drivers
            cat ${repos_enabled} | grep ID: | grep -q EOS_Mellanox && {
                echo -n "INFO: Disabling Mellanox repository from Satellite subscription..." 2>&1 | tee -a ${LOG_FILE}
                subscription-manager repos --disable=EOS_Mellanox* >> ${LOG_FILE}
                echo "Done." 2>&1 | tee -a ${LOG_FILE} && sleep 1
            }
            cat ${repos_enabled} | grep ID: | grep -q EOS_EPEL && {
                echo "INFO: CORTX_EPEL repository is enabled from Satellite subscription" 2>&1 | tee -a ${LOG_FILE}
            } || {
                #echo "INFO: Installing the Public Epel repository" 2>&1 | tee -a ${LOG_FILE}
                echo "INFO: Creating custom Epel repository" 2>&1 | tee -a ${LOG_FILE}
                #yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm 2>&1 | tee -a ${LOG_FILE}
                if [[ "$bundled_release" == true ]]; then
                    create_commons_repo_rhel "epel" "$epel_repo"
                else
                    create_commons_repo_rhel "satellite-epel" "http://ssc-satellite1.colo.seagate.com/pulp/repos/EOS/Library/custom/EPEL-7/EPEL-7/"
                fi
            }
            cat ${repos_all} | grep -q rhel-ha-for-rhel-7-server-rpms && {
                echo -n "INFO: RHEL HA repository is available from subscription, enabling it...." 2>&1 | tee -a ${LOG_FILE}
                subscription-manager repos --enable rhel-ha-for-rhel-7-server-rpms >> ${LOG_FILE}
                echo "Done." 2>&1 | tee -a ${LOG_FILE} && sleep 1
            } || {
                echo "ERROR: RHEL HA license is not available... Can not proceed" | tee -a ${LOG_FILE}
                echo "Please:" | tee -a ${LOG_FILE}
                echo "   1. Install RHEL High Availability license on the cluster nodes & rerun the command" | tee -a ${LOG_FILE}
                echo "       OR" | tee -a ${LOG_FILE}
                echo "   2. Disable subscription manager. Rerun the command with --disable-sub-mgr option" | tee -a ${LOG_FILE}
                echo "exiting..." | tee -a ${LOG_FILE}
                exit 1
                #echo "INFO: Creating repo for in house built HA packages" 2>&1 | tee -a ${LOG_FILE}
                #create_commons_repo_rhel "cortx_rhel_ha" "$url_local_repo_rhel_ha"
            }

            # Create commons repo for installing mellanox drivers
            echo "INFO: Enabling repo for in house built commons packages for Cortx" 2>&1 | tee -a ${LOG_FILE}
            create_commons_repo_rhel "cortx_commons" "$url_local_repo_commons_rhel"

            echo "INFO: Taking backup of /etc/yum.repos.d/*.repo to ${_bkpdir}"
            yes | cp -rf /etc/yum.repos.d/*.repo ${_bkpdir}

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
        create_commons_repos "$url_local_repo_commons"
    }
fi

echo -n "INFO: Cleaning yum cache............................................." 2>&1 | tee -a ${LOG_FILE}
yum autoremove -y >> ${LOG_FILE}
yum clean all >> ${LOG_FILE}
echo "Done." 2>&1 | tee -a ${LOG_FILE} && sleep 1

# Install lspci command
rpm -qa|grep "pciutils-"|grep -qv "pciutils-lib" && {
    echo "INFO: pciutils package is already installed." 2>&1 | tee -a ${LOG_FILE}
} || {
    echo "INFO: Installing pciutils package" 2>&1 | tee -a ${LOG_FILE}
    yum install -y pciutils 2>&1 | tee -a ${LOG_FILE}
}
if ( lspci -d"15b3:*"|grep Mellanox ) ; then
    rpm -qa | grep -q mlnx-ofed-all && rpm -qa | grep -q mlnx-fw-updater && {
        echo "INFO: Mellanox Drivers are already installed." 2>&1 | tee -a ${LOG_FILE}
    } || {
        echo "INFO: Installing Mellanox drivers" 2>&1 | tee -a ${LOG_FILE}
        yum install -y mlnx-ofed-all mlnx-fw-updater 2>&1 | tee -a ${LOG_FILE}
        echo "INFO: Rebooting the system now" 2>&1 | tee -a ${LOG_FILE}
        do_reboot=true
    }
    echo "INFO: Installing sg3_utils" 2>&1 | tee -a ${LOG_FILE}
    yum install -y sg3_utils 2>&1 | tee -a ${LOG_FILE}
    echo "INFO: Scanning SCSI bus............................................" | tee -a ${LOG_FILE}
    /usr/bin/rescan-scsi-bus.sh -a >> ${LOG_FILE}
fi

echo -n "INFO: Disabling default time syncronization mechanism..........." 2>&1 | tee -a ${LOG_FILE}
if [ `rpm -qa chrony` ]; then
    systemctl stop chronyd && systemctl disable chronyd &>> ${LOG_FILE}
    yum remove -y chrony &>> ${LOG_FILE}
fi
echo "Done." 2>&1 | tee -a ${LOG_FILE}


echo -e "\n***** SUCCESS!!! *****" 2>&1 | tee -a ${LOG_FILE}
echo "For more details see: $LOG_FILE"
if [[ "$do_reboot" == true ]]; then
    echo "INFO: Rebooting the system now" 2>&1 | tee -a ${LOG_FILE}
    shutdown -r now
fi
