#!/usr/bin/sh
unalias cp
set -e

if [[ -d '/opt/seagate/ees-prvsnr' ]]; then
  BASEDIR=/opt/seagate/ees-prvsnr
else
  BASEDIR=/opt/seagate/eos-prvsnr
fi

################
# Cleanup repos
################
[[ -f /etc/yum.repos.d/epel.repo.rpmsave ]] && sudo rm -rf /etc/yum.repos.d/epel.repo.*
[[ -f /etc/yum.repos.d/CentOS-Base.repo ]] && sudo rm -rf /etc/yum.repos.d/*.repo
sudo cp ${BASEDIR}/files/etc/yum.repos.d/*.repo /etc/yum.repos.d/

# Uncomment only if necessary
sudo yum clean all
sudo rm -rf /var/cache/yum
# yum update
# yum makecache fast

####################
# salt-minion setup
####################
# Ensure salt-minion uses python3
# sudo yum remove -y salt salt-ssh salt-minion
sudo yum install -y salt-ssh salt-minion salt-master

# Update master & minion config
sudo cp ${BASEDIR}/files/etc/salt/minion /etc/salt/minion
sudo cp ${BASEDIR}/files/etc/salt/master /etc/salt/master

sudo systemctl enable salt-master
sudo systemctl restart salt-master
sudo systemctl enable salt-minion
sudo systemctl restart salt-minion

# Disable salt-master as we would execute provisioning on-demand
# sudo systemctl stop salt-master
# sudo systemctl disable salt-master

# Disable salt-minion as we would execute provisioning on-demand
# sudo systemctl stop salt-minion
# sudo systemctl disable salt-minion

################
# Network setup
################
sudo cp -R ${BASEDIR}/files/etc/hosts /etc/hosts

# TODO: To be converted to a salt formula
if [[ -n "$(rpm -qi NetworkManager | grep "^Version" 2>/dev/null)" ]]; then
  sudo systemctl stop NetworkManager
  sudo systemctl disable NetworkManager
  sudo yum remove -y NetworkManager
fi

sudo cp -R ${BASEDIR}/files/etc/modprobe.d/bonding.conf /etc/modprobe.d/bonding.conf

# For HW setup
# sudo rm -f /etc/sysconfig/network-scripts/ifcfg-enp0s3
# sudo sed -i 's/BOOTPROTO=static/BOOTPROTO=dhcp/g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
# sudo sed -i 's/IPADDR=//g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
# sudo sed -i 's/BOOTPROTO=static/BOOTPROTO=dhcp/g' /etc/sysconfig/network-scripts/ifcfg-data0
# sudo sed -i 's/IPADDR=//g' /etc/sysconfig/network-scripts/ifcfg-data0
# sudo systemctl restart network.service

sudo mkdir -p ~/.ssh
sudo chmod -R 755 ~/.ssh
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr ~/.ssh/id_rsa
sudo chmod -R 400 ~/.ssh/id_rsa
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr.pub ~/.ssh/id_rsa.pub
sudo chmod -R 644 ~/.ssh/id_rsa.pub
sudo cp ${BASEDIR}/files/.ssh/authorized_keys ~/.ssh/authorized_keys
sudo chmod -R 644 ~/.ssh/authorized_keys
sudo cp ${BASEDIR}/files/.ssh/known_hosts ~/.ssh/known_hosts
sudo chmod -R 644 ~/.ssh/known_hosts
sudo cp ${BASEDIR}/files/.ssh/ssh_config ~/.ssh/ssh_config
sudo chmod -R 644 ~/.ssh/ssh_config

sudo mkdir -p /etc/salt/pki/master/ssh
sudo chmod -R 755 /etc/salt/pki/master/ssh
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr /etc/salt/pki/master/ssh/salt-ssh.rsa
sudo chmod -R 400 /etc/salt/pki/master/ssh/salt-ssh.rsa
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr.pub /etc/salt/pki/master/ssh/salt-ssh.rsa.pub
sudo chmod -R 644 /etc/salt/pki/master/ssh/salt-ssh.rsa.pub
