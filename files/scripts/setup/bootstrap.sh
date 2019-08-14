#!/usr/bin/sh
unalias cp
set -e

################
# Cleanup repos
################
sudo yum remove epel-release -y
[[ -f /etc/yum.repos.d/epel.repo.rpmsave ]] && sudo rm -rf /etc/yum.repos.d/epel.repo.*
[[ -f /etc/yum.repos.d/CentOS-Base.repo ]] && sudo rm -rf /etc/yum.repos.d/*.repo
sudo cp -R /opt/seagate/ees-prvsnr/files/etc/yum.repos.d/* /etc/yum.repos.d/

# Uncomment only if necessary
# sudo yum clean all
# sudo rm -rf /var/cache/yum
# yum update
# yum makecache fast

####################
# salt-minion setup
####################
# Ensure salt-minion uses python3
# sudo yum remove -y salt salt-ssh salt-minion
sudo yum install -y salt-ssh salt-minion salt-master

# Update master & minion config
sudo cp /opt/seagate/ees-prvsnr/files/etc/salt/minion /etc/salt/minion
sudo cp /opt/seagate/ees-prvsnr/files/etc/salt/master /etc/salt/master

# Disable salt-minion as we would execute provisioning on-demand
# sudo systemctl stop salt-minion
# sudo systemctl disable salt-minion

################
# Network setup
################
# TODO: To be converted to a salt formula
if [[ $(rpm -qi NetorkManager >/dev/null) ]]; then
  sudo systemctl stop NetworkManager
  sudo systemctl disable NetworkManager
  sudo yum remove -y NetworkManager
fi

sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-* /etc/sysconfig/network-scripts/
sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-mgmt0 /etc/sysconfig/network-scripts/
sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-data0 /etc/sysconfig/network-scripts/
sudo cp -R /opt/seagate/ees-prvsnr/files/etc/modprobe.d/bonding.conf /etc/modprobe.d/bonding.conf

# For HW setup
# sudo rm -f /etc/sysconfig/network-scripts/ifcfg-enp0s3
# sudo sed -i 's/BOOTPROTO=static/BOOTPROTO=dhcp/g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
# sudo sed -i 's/IPADDR=//g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
# sudo sed -i 's/BOOTPROTO=static/BOOTPROTO=dhcp/g' /etc/sysconfig/network-scripts/ifcfg-data0
# sudo sed -i 's/IPADDR=//g' /etc/sysconfig/network-scripts/ifcfg-data0
# sudo systemctl restart network.service

sudo mkdir -p /root/.ssh
sudo chmod -R 755 /root/.ssh
sudo cp /opt/seagate/ees-prvsnr/files/.ssh/id_rsa_prvsnr /root/.ssh/id_rsa
sudo chmod -R 400 /root/.ssh/id_rsa
sudo cp /opt/seagate/ees-prvsnr/files/.ssh/id_rsa_prvsnr.pub /root/.ssh/id_rsa.pub
sudo chmod -R 644 /root/.ssh/id_rsa.pub
sudo cp /opt/seagate/ees-prvsnr/files/.ssh/authorized_keys /root/.ssh/authorized_keys
sudo chmod -R 644 /root/.ssh/authorized_keys

sudo mkdir -p /etc/salt/pki/master/ssh
sudo chmod -R 755 /etc/salt/pki/master/ssh
sudo cp /opt/seagate/ees-prvsnr/files/.ssh/id_rsa_prvsnr /etc/salt/pki/master/ssh/salt-ssh.rsa
sudo chmod -R 400 /etc/salt/pki/master/ssh/salt-ssh.rsa
sudo cp /opt/seagate/ees-prvsnr/files/.ssh/id_rsa_prvsnr.pub /etc/salt/pki/master/ssh/salt-ssh.rsa.pub
sudo chmod -R 644 /etc/salt/pki/master/ssh/salt-ssh.rsa.pub
