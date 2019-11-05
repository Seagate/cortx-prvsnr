#!/usr/bin/sh
unalias cp
set -e

if [[ -d '/opt/seagate/ees-prvsnr' ]]; then
  BASEDIR=/opt/seagate/ees-prvsnr
else
  BASEDIR=/opt/seagate/eos-prvsnr
fi

# Cleanup old yum repos
sudo yum remove epel-release -y
[[ -f /etc/yum.repos.d/epel.repo.rpmsave ]] && sudo rm -rf /etc/yum.repos.d/epel.repo.*
[[ -f /etc/yum.repos.d/CentOS-Base.repo ]] && sudo rm -rf /etc/yum.repos.d/*.repo

# Setup yum repos as required for EOS
sudo cp -f ${BASEDIR}/files/etc/yum.repos.d/* /etc/yum.repos.d

# Uncomment only if necessary
# sudo yum clean all
# sudo rm -rf /var/cache/yum
# yum update
# yum makecache fast

################
# Network setup
################
# TODO: To be converted to a salt formula
if [[ -n "$(rpm -qi NetworkManager | grep "^Version" 2>/dev/null)" ]]; then
  sudo systemctl stop NetworkManager
  sudo systemctl disable NetworkManager
  sudo yum remove -y NetworkManager
fi

sudo cp ${BASEDIR}/files/etc/sysconfig/network-scripts/ifcfg-* /etc/sysconfig/network-scripts/
sudo cp ${BASEDIR}/files/etc/sysconfig/network-scripts/ifcfg-mgmt0 /etc/sysconfig/network-scripts/
sudo cp ${BASEDIR}/files/etc/sysconfig/network-scripts/ifcfg-data0 /etc/sysconfig/network-scripts/
sudo cp -R ${BASEDIR}/files/etc/modprobe.d/bonding.conf /etc/modprobe.d/bonding.conf

# Up the correct network interfaces.
sudo ifdown enp0s8
sudo ifdown enp0s9
sudo ifdown data0
sudo ifdown mgmt0
sudo ifup data0
sudo ifup mgmt0

# Setup the hosts file for VMs
sudo cat ${BASEDIR}/files/etc/hosts >> /etc/hosts

# TODO: set ssh keys for ssh to VMs
