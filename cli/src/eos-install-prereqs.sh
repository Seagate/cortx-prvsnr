#!/bin/bash

set -eu

if [[ $# -gt 0 ]]; then
    if [[ "$1" = "no-reboot" ]]; then
        echo "no-reboot option is depricated now, you can skip it next time,"\
             " with the new changes the system won't reboot if mlnx drivers are already installed."
    else
        echo "invalid option provided"
	exit 1
    fi
fi

echo "Checking If the hostnames are ok"
eosnode_hostname=`hostname -f`
if [[ $eosnode_hostname != *"."* ]]; then
      l_error "'hostname -f' did not return the FQDN, please set FQDN and retry."
      exit 1
fi
echo "INFO: hostname is OK: $eosnode_hostname"

echo "INFO: Checking if kernel version is correct"
kernel_version=`uname -r`
if [[ "$kernel_version" != '3.10.0-1062.el7.x86_64' ]]; then
    echo "ERROR: Kernel version is wrong. Required: 3.10.0-1062.el7.x86_64, installed: $kernel_version"
    exit 1
}

grep -q "Red Hat" /etc/*-release && { 
    echo "INFO: Chekcking if RHEL subscription manager is enabled"
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
                echo "ERROR: repo $repo is not enabled, checking if it's available"
                subscription-manager repos --list | grep ID | grep $repo && {
                    echo "Enabling repo $repo"
                    subscription-manager repos --enable $repo 
                    echo "INFO: Checking again if $repo is enabled"
                    subscription-manager repos --list | grep ID | grep $repo && {
                        echo "INFO: Repo $repo is enabled"
                    } || {
                        echo "ERROR: Repo $repo is not available, exiting..."
                        exit 1
                    }
                }
            }
        done
        echo "INFO: Installing yum-plugin-versionlock"
        yum install -y yum-plugin-versionlock
        echo "INFO: Restricting the kernel updates to current kernel version"
        yum versionlock kernel-3.10.0-1062.el7.x86_64
    fi
}

#echo "INFO: disabling the Red Hat Subscription Manager"
#subscription-manager auto-attach --disable || true
#subscription-manager remove --all || true
#subscription-manager unregister || true
#subscription-manager clean || true
#subscription-manager config --rhsm.manage_repos=0


echo "INFO: Creating repos for Lyve"
curl -# -o lyve_platform.tar http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/lyve_platform.tar
tar -xf lyve_platform.tar -C /etc/yum.repos.d/

echo "INFO: Cleaning yum cache"
yum clean all

hostnamectl status | grep Chassis | grep -q server && {
        rpm -qa | grep -q mlnx-ofed-all && rpm -qa | grep -q mlnx-fw-updater && {
            echo "Mellanox Drivers are already installed."
        } || {
            echo "INFO: Installing Mellanox drivers"
            yum install -y mlnx-ofed-all mlnx-fw-updater
            echo "INFO: Rebooting the system now"
            shutdown -r now
        }
    }
}
echo "Done"