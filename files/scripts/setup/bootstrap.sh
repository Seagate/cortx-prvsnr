#!/usr/bin/sh
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

unalias cp || true
set -e

if [[ -d '/opt/seagate/cortx-prvsnr' ]]; then
  BASEDIR=/opt/seagate/cortx-prvsnr
else
  BASEDIR=/opt/seagate/cortx/provisioner
fi

################
# Reset repos
################
# ToDo: Improve logic to setup repos based on target platform
[[ -f /etc/yum.repos.d/epel.repo.rpmsave ]] && sudo rm -rf /etc/yum.repos.d/epel.repo.*
#[[ -f /etc/yum.repos.d/CentOS-Base.repo ]] && sudo rm -rf /etc/yum.repos.d/*.repo
sudo cp ${BASEDIR}/files/etc/yum.repos.d/*.repo /etc/yum.repos.d/

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

# Update salt-master config
sudo cp ${BASEDIR}/cortx/srv/provisioner/salt_minion/files/minion /etc/salt/minion
sudo sed -i "s/master:.*/master: $(hostname)/g" /etc/salt/minion
# Update salt-master config
sudo cp ${BASEDIR}/cortx/srv/provisioner/salt_master/files/master /etc/salt/master

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
# if [[ -n "$(rpm -qi NetworkManager | grep "^Version" 2>/dev/null)" ]]; then
#   sudo systemctl stop NetworkManager
#   sudo systemctl disable NetworkManager
#   sudo yum remove -y NetworkManager
# fi

# sudo cp -R ${BASEDIR}/files/etc/modprobe.d/bonding.conf /etc/modprobe.d/bonding.conf

# For HW setup
# sudo rm -f /etc/sysconfig/network-scripts/ifcfg-enp0s3
# sudo sed -i 's/BOOTPROTO=static/BOOTPROTO=dhcp/g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
# sudo sed -i 's/IPADDR=//g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
# sudo sed -i 's/BOOTPROTO=static/BOOTPROTO=dhcp/g' /etc/sysconfig/network-scripts/ifcfg-data0
# sudo sed -i 's/IPADDR=//g' /etc/sysconfig/network-scripts/ifcfg-data0
# sudo systemctl restart network.service

sudo mkdir -p /root/.ssh
sudo chmod -R 755 /root/.ssh
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr /root/.ssh/id_rsa
sudo chmod -R 400 /root/.ssh/id_rsa
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr.pub /root/.ssh/id_rsa.pub
sudo chmod -R 644 /root/.ssh/id_rsa.pub
sudo cp ${BASEDIR}/files/.ssh/authorized_keys /root/.ssh/authorized_keys
sudo chmod -R 644 /root/.ssh/authorized_keys
sudo cp ${BASEDIR}/files/.ssh/known_hosts /root/.ssh/known_hosts
sudo chmod -R 644 /root/.ssh/known_hosts
sudo cp ${BASEDIR}/files/.ssh/config /root/.ssh/config
sudo chmod -R 644 /root/.ssh/config

sudo mkdir -p /etc/salt/pki/master/ssh
sudo chmod -R 755 /etc/salt/pki/master/ssh
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr /etc/salt/pki/master/ssh/salt-ssh.rsa
sudo chmod -R 400 /etc/salt/pki/master/ssh/salt-ssh.rsa
sudo cp ${BASEDIR}/files/.ssh/id_rsa_prvsnr.pub /etc/salt/pki/master/ssh/salt-ssh.rsa.pub
sudo chmod -R 644 /etc/salt/pki/master/ssh/salt-ssh.rsa.pub
