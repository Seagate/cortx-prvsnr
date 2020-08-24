#!/bin/bash

set -euE

export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/pre-unboxing-hf.log}"
mkdir -p $(dirname "${LOG_FILE}")
truncate -s 0 ${LOG_FILE}

PRVSNR_ROOT="/opt/seagate/eos-prvsnr"

node_list=("srvnode-1" "srvnode-2")
new_hostname_nodeA=
new_hostname_nodeB=
default_hostname_nodeA="cortx-node-a"
default_hostname_nodeB="cortx-node-b"
ssh_cmd="ssh -i /root/.ssh/id_rsa_prvsnr -o \"StrictHostKeyChecking no\""

function trap_handler {
    echo "***** ERROR! *****"
    echo "For detailed error logs, please see: $LOG_FILE"
    echo "******************"
}
trap trap_handler ERR

sub_manager_check()
{
    _node="${1:-srvnode-1}"

    grep -q "Red Hat" /etc/*-release || {
        echo "$_node is not a RedHat system" | tee -a ${LOG_FILE}
        subscription_enabled=false
        return
    }

    echo "Checking if RHEL subscription manager is enabled on $_node" 2>&1 | tee -a ${LOG_FILE}
    subc_list=`ssh $_node subscription-manager list | grep Status: | awk '{ print $2 }'`
    subc_status=`ssh $_node subscription-manager status | grep "Overall Status:" | awk '{ print $3 }'`
    if echo "$subc_list" | grep -q "Subscribed"; then
        if [[  "$subc_status" == "Current" ]]; then
            echo "RedHat subscription manager is enabled on $_node." 2>&1 | tee -a ${LOG_FILE}
            subscription_enabled=true
        else
            echo "RedHat subscription manager is disabled on $_node." 2>&1 | tee -a ${LOG_FILE}
            subscription_enabled=false
        fi
    fi
}

sub_manager_cleanup()
{
    _node="${1:-srvnode-1}"
    grep -q "Red Hat" /etc/*-release || {
        echo "$_node is not a RedHat system" | tee -a ${LOG_FILE}
        return
    }
    echo "Cleaning up the subscription manager on $_node" | tee -a ${LOG_FILE}

    echo "Running the subscription-manager auto-attach on $_node" | tee -a ${LOG_FILE}
    ssh $_node subscription-manager auto-attach --disable || true  | tee -a ${LOG_FILE}

    echo "Running subscription-manager remove --all on $_node" | tee -a ${LOG_FILE}
    ssh $_node subscription-manager remove --all || true | tee -a ${LOG_FILE}

    echo "Running subscription-manager unregister on $_node" | tee -a ${LOG_FILE}
    ssh $_node subscription-manager unregister || true | tee -a ${LOG_FILE}

    echo "Running subscription-manager clean on $_node" | tee -a ${LOG_FILE}
    ssh $_node subscription-manager clean || true | tee -a ${LOG_FILE}

    echo "Running subscription-manager config --rhsm.manage_repos=0 on $_node" | tee -a ${LOG_FILE}
    ssh $_node subscription-manager config --rhsm.manage_repos=0 | tee -a ${LOG_FILE}
}

seagate_refs_cleanup()
{
    for _node in "${node_list[@]}"; do
        subscription_enabled=false
        sub_manager_check "$_node"
        if [[ "$subscription_enabled" == true ]]; then
            sub_manager_cleanup "$_node"
        fi

        echo "Removing following repos from $_node" | tee -a ${LOG_FILE}
        ssh "$_node" 'grep -lE "seagate.com" /etc/yum.repos.d/*.repo' | tee -a ${LOG_FILE}

        ssh "$_node" 'for file in `grep -lE "seagate.com" /etc/yum.repos.d/*.repo`; do rm -f "$file"; done'
        echo "Cleaning yum cache on $_node" | tee -a ${LOG_FILE}
        ssh "$_node" 'yum clean all'

        echo "Done" | tee -a ${LOG_FILE}
    done
}

luns_availability_check()
{
    node_list=("srvnode-1" "srvnode-2")
    echo "Checking the luns from storage enclosure" | tee -a ${LOG_FILE}
    for _node in "${node_list[@]}"; do
        $ssh_cmd $_node 'lsblk -S| grep sas' | tee -a ${LOG_FILE}
        _nluns=$($ssh_cmd $node 'lsblk -S | grep sas | wc -l')
        echo "No of luns on server $_node are: $_nluns" | tee -a ${LOG_FILE}
        if [[ $_nluns -eq 0 || $_nluns -ne 32 ]]; then
            echo "Error: The luns from storage enclosure are not correct." | tee -a ${LOG_FILE}
            echo "Please make sure the storage enclosre is connected to servers as shown in the user guide" | tee -a ${LOG_FILE}
            echo "Try rebooting the nodes the nodes are connected and the problem persists" | tee -a ${LOG_FILE}
            exit 1
        fi
        echo "The luns are OK on server $_node"  | tee -a ${LOG_FILE}
    done
}

new_hostname_get()
{
    _tnode=$1
    # Prompt user for the new hostname
    if [[ $_tnode == "srvnode-1" ]]; then
        read -p "Enter new hostname for server A(press enter to kee default [$default_hostname_nodeA]): " new_hostname_nodeA
        new_hostname_nodeA=${new_hostname_nodeA:-$default_hostname_nodeA}
    else
        read -p "Enter new hostname for server B(press enter to keep default [$default_hostname_nodeB]): " new_hostname_nodeA
        new_hostname_nodeB=${new_hostname_nodeB:-$default_hostname_nodeB}
    fi
}

new_hostname_set()
{
    _tnode=$1
    # Prompt user for the new hostname (suggest sample hostname as an example)
    echo "Setting the new hostname provided by user" | tee -a ${LOG_FILE}
    for _node in "${node_list[@]}"; do
        if [[ $_node == "srvnode-1" && ! -z $new_hostname_nodeA ]]; then
            echo "setting hostname($new_hostname_nodeA) for server A" | tee -a ${LOG_FILE}
            _nodename="server A"
            _new_hostname=$new_hostname_nodeA
        elif [[ $_node == "srvnode-2" && ! -z $new_hostname_nodeB ]]; then
            echo "setting hostname($new_hostname_nodeB) for server B" | tee -a ${LOG_FILE}
            _nodename="server B"
            _new_hostname=$new_hostname_nodeB
        else
            continue
        fi
        $ssh_cmd $_node 'chattr -i /etc/hostname' 2>&1 | tee -a ${LOG_FILE}
        $ssh_cmd $_node 'hostnamectl --set-hostnmae --static --transient --pretty $new_hostname_nodeA' 2>&1 | tee -a ${LOG_FILE}
        echo "waiting for the new hostname to get updated in system" | tee -a ${LOG_FILE}
        sleep 20
        _hostname=$($ssh_cmd $_node 'hostname')
        if [[ "$_hostname" == "$_new_hostname" ]]; then
            echo "New hostname($_new_hostname) is set successfully for $_nodename" | tee -a ${LOG_FILE}
        else
            echo "Error The hostname provided by user ($_new_hostname) could not be set for $_nodename" | tee -a ${LOG_FILE}
            echo "Please check the DNS setting or set the hostname manually and try again." | tee -a ${$LOG_FILE}
            exit 1
        fi
    done

}

hostname_validate_get_set()
{
    #3.1 print the current hostname
    #[check if there is .seagate.com name, if yes]
    #4. Get the hostname from the user (FQDN or not):
    #4.1 print out new names and ask for confirmation
    #5. Set the hostnames on the servers
    #5.0.1 Change attr to set the /etc/hostname (chattr -i /etc/hostname)
    #5.2 restart hostname service
    node_list=("srvnode-1" "srvnode-2")
    _seagate_hname=false

    echo "Running the hostname validation" | tee -a ${LOG_FILE}
    for _node in "${node_list[@]}"; do
        echo "Running hostname check on $_node" >> ${LOG_FILE}
        _hname=$($ssh_cmd $_node 'hostname')
        echo $_hname | grep -q "seagate.com" && $_seagate_hname=true || _seagate_hname=false
        if [[ $_seagate_hname == "true" ]]; then
            echo "Hostname of $_node has the seagate domain name" >> ${LOG_FILE}
            new_hostname_get $_node
        else
            echo "The hostname for $_node looks good" | tee -a ${LOG_FILE}
        fi
    done

    if [[ ! -z $new_hostname_nodeA || ! -z $new_hostname_nodeA ]]; then
        echo "New hostnames provided by user:" | tee -a ${LOG_FILE}
        if [[ ! -z $new_hostname_nodeA ]]; then
            echo "server A: $new_hostname_nodeA" | tee -a ${LOG_FILE}
        fi

        if [[ ! -z $new_hostname_nodeB ]]; then
            echo "server B: $new_hostname_nodeB" | tee -a ${LOG_FILE}
        fi
    fi

    new_hostname_set

}

dns_update_hostnames()
{
    # grab the IP address for MGMT interface from 'ip a' output
    # add the new names/IPs to /etc/hosts
    # Check if hostnames are getting resolved to mgmt ip addresses

    # Get management interface & ip address for it on node1
    local mgmt_if=$(grep -m1 -A3 -P "mgmt_nw:" ${PRVSNR_ROOT}/pillar/user/groups/all/cluster.sls|tail -1|cut -d'-' -f2|tr -d "[:space:]")
    local mgmt_ip_1=$((ip addr show dev ${mgmt_if}|grep inet|grep -v inet6|grep -Po "\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}" || echo "ERROR: IP address missing for ${mgmt_if} on srvnode-1" || (tee -a ${LOG_FILE}; exit 1))|head -1)
    echo "Management IP (Server A) : ${mgmt_ip_1}" | tee -a ${LOG_FILE}

    # Get management interface & ip address for it on node2
    local mgmt_ip_2=$((ssh -i /root/.ssh/id_rsa_prvsnr -o "StrictHostKeyChecking no" ${private_data_ip_node_2} "ip addr show dev ${mgmt_if}|grep inet|grep -v inet6|grep -Po \"\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}\"" || (echo "ERROR: IP address missing for ${mgmt_if} on srvnode-2" | tee -a ${LOG_FILE}; echo 1))|head -1)
    echo "Management IP (Server B) : ${mgmt_ip_2}" | tee -a ${LOG_FILE}

    # Add entries in /etc/hosts only if the hostnames are NOT getting resolved from each other
    echo "Checking if server B is reachable using new hostname($new_hostname_nodeB)" | tee -a ${LOG_FILE}
    if ping -c1 -W2  $new_hostname_nodeB > /dev/null; then
        echo "ERROR: Unable to ping server B ($new_hostname_nodeB) from server A ($new_hostname_nodeA)" |tee -a ${LOG_FILE}
        # Retry after adding entry in /etc/hosts
    else
        echo "Ok." | tee -a ${LOG_FILE}
    fi

    # check if entry in /etc/hosts is already added for mgmt_ip_1
    # if yes, ensure it's against new_hostname_nodeA, if not update it, else do nothing.
    if grep -q "${mgmt_ip_1}" /etc/hosts ; then
        # check if there are multiple/duplicate entries of ip addresses in /etc/hosts
        if [[ $(grep "${mgmt_ip_1}" /etc/hosts | wc -l) -ge 2 ]]; then
            echo "Error: Thre are multiple entries of ${mgmt_ip_1} in /etc/hosts, please correct them before proceeding ahead" | tee -a ${LOG_FILE}
            exit 1
        fi
        if grep "${mgmt_ip_1}" /etc/hosts | grep "${new_hostname_nodeA}"; then
            echo "/etc/hosts already has dns entry against ${mgmt_ip_1} for ${new_hostname_nodeA}" | tee -a ${LOG_FILE}
        else
            # Entry for ${mgmt_ip_1} is already there in /etc/hosts
            # but it's not against ${new_hostname_nodeA}
            #TODO: Handle this case.
            echo "Error: /etc/hosts already has entry for ${mgmt_ip_1} but against wrong hostname, please remove it manually" | tee -a  ${LOG_FILE}
            exit 1
        fi
    else
         # /etc/hosts does not has the entry, add it
         echo "$mgmt_ip_1 $new_hostname_nodeA" >> /etc/hosts
    fi
}

ssh_config_update()
{

}

minion_config_update()
{
    #6.1 restart minion service
    #6.2 (node-A only) restart master service

}

# 1. Run cleanup 
seagate_refs_cleanup

# 2. Check if the volumes are being listed on both the nodes - lsblk
luns_availability_check

#3. check if the hostname contains 'seagate.com'
hostname_validate_get_set

#4 update hostnames in local dns (/etc/hosts)
dns_update_hostnames

#5 Update hostnames in ssh config files
ssh_config_update

#6. Update minion files on both the nodes to point master to server A hostname
minion_config_update


#10. print ip a
ip a | tee -a ${LOG_FILE}

$ssh_cmd srvnode-2 'ip a' | tee -a ${LOG_FILE}
