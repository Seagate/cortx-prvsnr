#!/bin/bash

export LOG_FILE="/var/log/seagate/provisioner/private_inband.log"
mkdir -p $(dirname "${LOG_FILE}")
set -euE

function trap_handler {
    echo "***** ERROR! *****"
    echo "For detailed error logs, please see: $LOG_FILE"
    echo "******************"
}
trap trap_handler ERR

eno2_update()
{
    $ip=$1
    eno2_cfg=$2
    cat << EOF > \$eno2_cfg
DEVICE="eno2"
USERCTL="no"
TYPE="Ethernet"
BOOTPROTO="none"
ONBOOT="yes"
IPADDR="\$ip"
PREFIX="24"
PEERDNS="no"
DEFROUTE="no"
NM_CONTROLLED="no"
ZONE=trusted
EOF

}

# Update eno2 for srvnode-1
eno2_cfg="/etc/sysconfig/network-scripts/ifcfg-eno2"
eno2_cfg_tmp="/tmp/ifcfg-eno2-node-1"
echo "Updating eno2 on sever A with ip 10.0.0.4" | tee -a ${LOG_FILE}
eno2_update 10.0.0.4 $eno2_cfg_tmp
cp $eno2_cfg ${eno2_cfg}.bak
cp $eno2_cfg_tmp $eno2_cfg
echo "Restarting the eno2 interface on server A" | tee -a ${LOG_FILE}
ifdown eno2
ifup eno2
echo "Checking if the eno2 is updated with ip address" | tee -a ${LOG_FILE}
ip -o addr | grep eno2 | grep 10.0.0.4
echo "eno2 is successfully updated on server A" | tee -a ${LOG_FILE}

# Update eno2 for srvnode-2
echo "Updating eno2 on sever B with ip 10.0.0.5" | tee -a ${LOG_FILE}
eno2_cfg_tmp="/tmp/ifcfg-eno2-node-2"
eno2_update 10.0.0.5 $eno2_cfg_tmp

# Take back up of orignal ifcfg-eno2 file on srvnode-2
echo "Connecting to server-2 over ssh to copy the original eno2 config file" >> ${LOG_FILE}
ssh_cmd="ssh -i /root/.ssh/id_rsa_prvsnr -o \"StrictHostKeyChecking no\""
$ssh_cmd srvnode-2 'cp /etc/sysconfig/network-scripts/ifcfg-eno2 /etc/sysconfig/network-scripts/ifcfg-eno2.bak'
echo "Back created successfully" >> ${LOG_FILE}

# scp the newly generated ifcfg-eno2 file to srvnode-2
echo "scp the new eno2 config file on to server B" >> ${LOG_FILE}
scp -i /root/.ssh/id_rsa_prvsnr -o "StrictHostKeyChecking no" /tmp/ifcfg-eno2-node-2 srvnode-2:/etc/sysconfig/network-scripts/ifcfg-eno2
echo "done" >> ${LOG_FILE}
echo "Restarting the eno2 interface on server B" | tee -a ${LOG_FILE}
$ssh_cmd 'ifdown eno2'
$ssh_cmd 'ifup eno2'
$ssh_cmd 'ip -o addr | grep eno2 | grep 10.0.0.5'
echo "eno2 is successfully updated on server B" | tee -a ${LOG_FILE}

# node A => controller A
echo "Checking connectivity to controller A (10.0.0.2) from server A over private out-of-band channel " | tee -a ${LOG_FILE}
ping -c3 -W2 -Ieno2 10.0.0.2 || (echo "ERROR: Unable to ping controller A (10.0.0.2) from server A over eno2"; exit 1)
echo "Controller A is reachable from Server A over eno2" | tee -a ${LOG_FILE}

# node B => controller B
echo "Checking connectivity to controller B (10.0.0.3) from server B over private out-of-band channel " | tee -a ${LOG_FILE}
$ssh_cmd srvnode-2 'ping -c3 -W2 -Ieno2 10.0.0.3" || (echo \"ERROR: Unable to ping controller B from server B over eno2\"; exit 1)'
echo "Done" | tee -a ${LOG_FILE}

echo "Restarting the cluster services again" | tee -a ${LOG_FILE}
echo "Putting the cluster in maintenance mode" >> ${LOG_FILE}
hctl node maintenance --all --timeout-sec=600
echo "DEBUG: done" >> ${LOG_FILE} 
sleep 4
echo "Brining the cluster out from the maintenance mode" >> ${LOG_FILE}
hctl node unmaintenance --all --timeout-sec=600
echo "Done" | tee -a ${LOG_FILE}

echo "\
***** SUCCESS! *****

Run following commands manually to proceed:

1. Login to the controller A
ssh manage@10.0.0.2

2. After succeessfully logging in to controller A, run following command
show controllers

3. save the ouput of step 2 in some file e.g. /root/show_ctrl_output

4. exit from the controller shell, run:
exit 

5. Login to the Contrx UI from the browser using management VIP and check the dashboard for any error/alerts etc.
If any of the above command fails, please contact Seagate support.

" tee -a ${LOG_FILE}
