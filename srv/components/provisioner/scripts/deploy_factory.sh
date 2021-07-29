#!/bin/bash

set -eu

echo "FACTORY DEPLOYMENT"

############################# INPUT ###############
run_install_sh=true
# provide install_sh_url & target_build if run_install_sh is true
install_sh_path=
target_build=

SERVER_TYPE=   #"VM|HW"

# Network interfaces
data_if=      #For VM: "eth1"
pvt_if=       #For VM: "eth3"
mgmt_if=      #For VM: "eth0"

# SERVER NAMES
server_name=   #vm1  #e.g. server_name=server1

#BMC DETAILS
bmc_ip=       # For VM: "127.0.0.1"
bmc_user=     # For VM: "admin"
bmc_password= # For VM: 'admin'

#ENCLOSURE DETAILS
if [[ $SERVER_TYPE == "HW" ]]; then
    enc_primary_ip="10.0.0.2"
    enc_secondary_ip="10.0.0.3"
else
    enc_primary_ip="127.0.0.1"
    enc_secondary_ip="127.0.0.1"
fi

enc_user=     #"manage"
enc_password= #'!manage'
enc_port=80
enc_name=     #"virtual_enc"
enc_type=     #virtual"
ctrl_type=    #virtual"

#STORAGE DEVICES
# Run get_multipath_devs.sh to fill these variables:
data_devs_cvg0=     #For VM: "/dev/sdc,/dev/sdd"
md_devs_cvg0=       #For VM: "/dev/sdb"
data_devs_cvg1=     #For VM: "/dev/sde"
md_devs_cvg1=       #For VM: "/dev/sdf,/dev/sdg"

if [[ "$run_install_sh" == true ]]; then
    echo "Downloading the install.sh"
    mkdir -p /mnt/cortx/{components,dependencies,scripts}
    cd /mnt/cortx/scripts
    curl -O $install_sh_path
    chmod +x ./install.sh
    ./install.sh -t $target_build
fi

echo "Checking if cortx_setup -h works"
command -v cortx_setup

echo "Running cortx_setup server config"
#cortx_setup server config --name  $server_name --type $SERVER_TYPE

echo "Running cortx_setup network config"
#cortx_setup server config --name  $server_name --type $SERVER_TYPE
#cortx_setup network config --transport lnet
#cortx_setup network config --mode tcp
cortx_setup network config --interfaces $data_if --type data
cortx_setup network config --interfaces $pvt_if --type private
cortx_setup network config --interfaces $mgmt_if --type management

echo "Running cortx_setup BMC config"
cortx_setup network config --bmc $bmc_ip --user $bmc_user --password $bmc_password

echo "Running cortx_setup storage config"
if [[ $SERVER_TYPE == "HW" ]]; then
    ping -c1 $enc_primary_ip
    ping -c1 $enc_secondary_ip
fi
cortx_setup storage config --controller $ctrl_type --mode primary --ip $enc_primary_ip --port $enc_port --user $enc_user --password $enc_password
cortx_setup storage config --controller $ctrl_type --mode secondary --ip $enc_secondary_ip --port $enc_port --user $enc_user --password $enc_password
cortx_setup storage config --name $enc_name --type $enc_type
cortx_setup storage config --cvg 0 --data_devices $data_devs_cvg0 --metadata_devices $md_devs_cvg0
cortx_setup storage config --cvg 1 --data_devices $data_devs_cvg1 --metadata_devices $md_devs_cvg1

echo "Running cortx_setup configure security"
cortx_setup security config --certificate /opt/seagate/cortx/provisioner/srv/components/misc_pkgs/ssl_certs/files/stx.pem

echo "Running cortx_setup set/get config"
cortx_setup config set --key 'cortx>software>s3>service>instances' --val 1
cortx_setup config set --key 'cortx>software>s3>io>max_units' --val 2
cortx_setup config set --key 'cortx>software>motr>service>client_instances' --val 1

echo "Running cortx_setup node initialize"
cortx_setup node initialize

echo "Running cortx_setup signature set/get"
cortx_setup signature set --key LR_SIGNATURE --value HP1_5U84
cortx_setup signature get --key LR_SIGNATURE

if [[ $SERVER_TYPE == "HW" ]]; then
    echo "Running cortx_setup resource discover"
    cortx_setup resource discover
    cortx_setup resource show --health --resource_type 'node'
fi


echo "Running cortx_setup node finalize"
if [[ $SERVER_TYPE == "HW" ]]; then
    cortx_setup node finalize --force
else
    cortx_setup node finalize --force || true
fi

echo "FACTORY DEPLOYMENT SUCCESS!!!"


