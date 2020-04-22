#!/bin/bash

set -eu

export LOG_FILE=/var/log/seagate/provisioner/deploy-eos.log
mkdir -p $(dirname "${LOG_FILE}")
/usr/bin/true > ${LOG_FILE}

if [[ $# -gt 0 ]]; then
    if [[ "$1" = "no-reboot" ]]; then
        echo "no-reboot option is depricated now, you can skip it next time,"\
             " with the new changes the system won't reboot if mlnx drivers are already installed." 2>&1 | tee ${LOG_FILE}
    else
        echo "ERROR: Invalid option provided"  2>&1 | tee ${LOG_FILE}
	exit 1
    fi
fi

echo "Checking If the hostnames are ok" 2>&1 | tee ${LOG_FILE}
eosnode_hostname=`hostname -f`
if [[ $eosnode_hostname != *"."* ]]; then
      echo "ERROR: 'hostname -f' did not return the FQDN, please set FQDN and retry."  2>&1 | tee ${LOG_FILE}
      exit 1
fi
echo "INFO: hostname is OK: $eosnode_hostname" 2>&1 | tee ${LOG_FILE}

echo "INFO: Checking if kernel version is correct" 2>&1 | tee ${LOG_FILE}
kernel_version=`uname -r`
if [[ "$kernel_version" != '3.10.0-1062.el7.x86_64' ]]; then
    echo "ERROR: Kernel version is wrong. Required: 3.10.0-1062.el7.x86_64, installed: $kernel_version" 2>&1 | tee ${LOG_FILE}
    exit 1
}

grep -q "Red Hat" /etc/*-release && { 
    echo "INFO: Chekcking if RHEL subscription manager is enabled" 2>&1 | tee ${LOG_FILE}
    subc_list=`subscription-manager list | grep Status: | awk '{ print $2 }'`
    subc_status=`subscription-manager status | grep "Overall Status:" | awk '{ print $3 }'`

    if [[ "$subc_list" = "Subscribed" && "$subc_status" = "Current" ]]; then
        # Ensure required repos are enabled in subscription
        repos_list=(
            "EOS_Mellanox_mlnx_ofed-4_7-3_2_9_0"
            "EOS_EPEL-7_EPEL-7"
            "rhel-7-server-optional-rpms"
            "rhel-7-server-satellite-tools-6.6-rpms"
            "rhel-7-server-rpms"
            "rhel-7-server-extras-rpms"
            "rhel-7-server-supplementary-rpms"
            "EOS_Puppet6_puppet6-el7"
            "rhel-ha-for-rhel-7-server-rpms"
        )
        for repo in ${repos_list[@]}
        do
            subscription-manager repos --list-enabled | grep ID | grep $repo || {
                echo "ERROR: repo $repo is not enabled, checking if it's available" 2>&1 | tee ${LOG_FILE}
                subscription-manager repos --list | grep ID | grep $repo && {
                    echo "INFO: Enabling repo $repo" 2>&1 | tee ${LOG_FILE}
                    subscription-manager repos --enable $repo 
                    echo "INFO: Checking again if $repo is enabled" 2>&1 | tee ${LOG_FILE}
                    subscription-manager repos --list | grep ID | grep $repo && {
                        echo "INFO: Repo $repo is enabled" 2>&1 | tee ${LOG_FILE}
                    } || {
                        echo "ERROR: Repo $repo is not available, exiting..." 2>&1 | tee ${LOG_FILE}
                        exit 1
                    }
                }
            }
        done
        echo "INFO: Installing yum-plugin-versionlock" 2>&1 | tee ${LOG_FILE}
        yum install -y yum-plugin-versionlock
        echo "INFO: Restricting the kernel updates to current kernel version" 2>&1 | tee ${LOG_FILE}
        yum versionlock kernel-3.10.0-1062.el7.x86_64
    fi
}

#echo "INFO: disabling the Red Hat Subscription Manager"
#subscription-manager auto-attach --disable || true
#subscription-manager remove --all || true
#subscription-manager unregister || true
#subscription-manager clean || true
#subscription-manager config --rhsm.manage_repos=0


echo "INFO: Creating repos for Lyve" 2>&1 | tee ${LOG_FILE}
curl -# -o lyve_platform.tar http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/lyve_platform.tar
tar -xf lyve_platform.tar -C /etc/yum.repos.d/

echo "INFO: Cleaning yum cache" 2>&1 | tee ${LOG_FILE}
yum clean all

hostnamectl status | grep Chassis | grep -q server && {
        rpm -qa | grep -q mlnx-ofed-all && rpm -qa | grep -q mlnx-fw-updater && {
            echo "INFO: Mellanox Drivers are already installed." 2>&1 | tee ${LOG_FILE}
        } || {
            echo "INFO: Installing Mellanox drivers" 2>&1 | tee ${LOG_FILE}
            yum install -y mlnx-ofed-all mlnx-fw-updater
            echo "INFO: Rebooting the system now" 2>&1 | tee ${LOG_FILE}
            shutdown -r now
        }
    }
}
echo "INFO: Done" 2>&1 | tee ${LOG_FILE}