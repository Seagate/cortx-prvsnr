#!/bin/bash

set -eu

echo "FACTORY DEPLOYMENT"

# Inputs needed
install_sh_path="https://raw.githubusercontent.com/Seagate/cortx-prvsnr/pre-cortx-1.0/srv/components/provisioner/scripts/install.sh"

############################# INPUT FOR NODE1 ############### 

target_build=

# Network interfaces
data_if_n1=""
pvt_if_n1=""
mgmt_if_n1=""

# SERVER NAMES
server_name=  #e.g. server_name=server1

#BMC DETAILS
bmc_ip=""
bmc_user=""
bmc_password=''

#ENCLOSURE DETAILS
enc_user=""
enc_password=''
enc_port=80
enc_mode="primary" #use secondary for secondary nodes
enc_name=""
enc_type="RBOD"

#STORAGE DEVICES
# Run get_multipath_devs.sh to fill these variables:
data_devs_cvg0=""
md_devs_cvg0=""
data_devs_cvg1=""
md_devs_cvg1=""

echo "Downloading the install.sh"
mkdir -p /mnt/cortx/{components,dependencies,scripts}
cd /mnt/cortx/scripts
curl -O $install_sh_path
chmod +x ./install.sh 
./install.sh -t $target_build

echo "Checking if cortx_setup -h works"
command -v cortx_setup

echo "Running cortx_setup server config"
cortx_setup server config --name  $server_name --type HW

echo "Running cortx_setup network config"
cortx_setup server config --name  $server_name --type HW
cortx_setup network config --transport lnet
cortx_setup network config --mode tcp
cortx_setup network config --interfaces $data_if --type data
cortx_setup network config --interfaces $pvt_if --type private
cortx_setup network config --interfaces $mgmt_if --type management

echo "Running cortx_setup BMC config"
cortx_setup network config --bmc $bmc_ip --user $bmc_user --password $bmc_password

echo "Running cortx_setup storage config"
ping -c1 10.0.0.2
ping -c1 10.0.0.3
cortx_setup storage config --controller gallium --mode $enc_mode --ip 10.0.0.2 --port $enc_port --user $enc_user --password $enc_password
cortx_setup storage config --name $enc_name --type $enc_type
cortx_setup storage config --cvg 0 --data_devices $data_devs_cvg0 --metadata_devices $md_devs_cvg0
cortx_setup storage config --cvg 1 --data_devices $data_devs_cvg1 --metadata_devices $md_devs_cvg1

echo "Running cortx_setup configure security"
cortx_setup security config --certificate /opt/seagate/cortx/provisioner/srv/components/misc_pkgs/ssl_certs/files/stx.pem

echo "Running cortx_setup set/get config"
cortx_setup config set --key 'cortx>software>s3>service>instances' --val 11
cortx_setup config set --key 'cortx>software>s3>io>max_units' --val 32
cortx_setup config set --key 'cortx>software>motr>service>client_instances' --val 2

echo "Running cortx_setup node initialize"
cortx_setup node initialize

echo "Running cortx_setup signature set/get"
cortx_setup signature set --key LR_SIGNATURE --value HP1_5U84
cortx_setup signature get --key LR_SIGNATURE

echo "Running cortx_setup resource discover"
cortx_setup resource discover
cortx_setup resource show --health --resource_type 'node'

echo "Running cortx_setup node finalize"
cortx_setup node finalize --force

echo "FACTORY DEPLOYMENT SUCCESS!!!"


