#!/bin/bash

set -euE

export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/pre-unboxing-hf.log}"
mkdir -p $(dirname "${LOG_FILE}")
truncate -s 0 ${LOG_FILE}

PRVSNR_ROOT="/opt/seagate/eos-prvsnr"

node_list=("srvnode-1" "srvnode-2")
new_hostname_nodeA=
new_hostname_nodeB=
hostname_A=
hostname_B=
default_hostname_nodeA="cortx-node-a"
default_hostname_nodeB="cortx-node-b"
private_data_ip_node_1="192.169.0.1"
private_data_ip_node_2="192.169.0.2"
ssh_cmd="ssh -i /root/.ssh/id_rsa_prvsnr -o \"StrictHostKeyChecking no\""
scp_cmd="scp -i /root/.ssh/id_rsa_prvsnr -o \"StrictHostKeyChecking no\""

function trap_handler {
    echo "***** ERROR! *****"
    echo "For detailed error logs, please see: $LOG_FILE"
    echo "******************"
}
trap trap_handler ERR

echo "DEBUG: private_data_ip_node_1: $private_data_ip_node_1" >> ${LOG_FILE}
echo "DEBUG: private_data_ip_node_2: $private_data_ip_node_2" >> ${LOG_FILE}

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
    node_list=("\${private_data_ip_node_1}" "\${private_data_ip_node_2}")
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
    # Prompt user for the new hostname (suggest sample hostname as an example)

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
        #TODO: Which service to restart to get the hostname updated in customer's DNS server?
        _hostname=$($ssh_cmd $_node 'hostname')
        if [[ "$_hostname" == "$_new_hostname" ]]; then
            echo "New hostname($_new_hostname) is set successfully for $_nodename" | tee -a ${LOG_FILE}
        else
            echo "Error The hostname provided by user ($_new_hostname) could not be set for $_nodename" | tee -a ${LOG_FILE}
            echo "Please check the DNS setting or set the hostname manually and try again." | tee -a ${$LOG_FILE}
            exit 1
        fi
        if [[ $_node == "srvnode-1" ]]; then hostname_A=${_hostname}; else hostname_B=${_hostname}; fi 
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
            if [[ $_node == "srvnode-1" ]]; then
                hostname_A=${_hname}
                echo "hostname of server A: ${hostname_A}" | tee -a ${LOG_FILE}
            else
                hostname_B=${_hname}
                echo "hostname of server B: ${hostname_B}" | tee -a ${LOG_FILE}
            fi
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
    # Check if hostnames are getting resolved to mgmt ip addresses
    # Add the new names/IPs to /etc/hosts

    # Get management interface name from pillar
    local mgmt_if=$(grep -m1 -A3 -P "mgmt_nw:" ${PRVSNR_ROOT}/pillar/user/groups/all/cluster.sls|tail -1|cut -d'-' -f2|tr -d "[:space:]")

    # Get management interface ip address for node1
    local mgmt_ip_A=$((ip addr show dev ${mgmt_if}|grep inet|grep -v inet6|grep -Po "\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}" || echo "ERROR: IP address missing for ${mgmt_if} on srvnode-1" || (tee -a ${LOG_FILE}; exit 1))|head -1)
    echo "Management IP (Server A) : ${mgmt_ip_A}" | tee -a ${LOG_FILE}

    # Get management ip address for node2
    local mgmt_ip_B=$((ssh -i /root/.ssh/id_rsa_prvsnr -o "StrictHostKeyChecking no" ${private_data_ip_node_2} "ip addr show dev ${mgmt_if}|grep inet|grep -v inet6|grep -Po \"\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}\"" || (echo "ERROR: IP address missing for ${mgmt_if} on srvnode-2" | tee -a ${LOG_FILE}; echo 1))|head -1)
    echo "Management IP (Server B) : ${mgmt_ip_B}" | tee -a ${LOG_FILE}

    # Check if entries in /etc/hosts needs to be added.
    # The entry needs to be added only if the hostnames are NOT getting resolved from each other
    echo "Checking if server B ($hostname_B) is reachable from server A ($hostname_A) over DNS" | tee -a ${LOG_FILE}
    if ping -c1 -W2  $hostname_B > /dev/null; then
        # Ping is successfull, no need to add entry in /etc/hosts
        echo "Server B ($hostname_B) is reachable from ServerA ($hostname_A) over DNS" | tee -a ${LOG_FILE}
        _ping_status_A_to_B=true
    else
        # Ping failed, need to add entry in /etc/hosts
        echo "ERROR: Server B ($hostname_B) is not reachable from server A ($hostname_A) over DNS" |tee -a ${LOG_FILE}
        _ping_status_A_to_B=false
    fi

    echo "Checking if server A ($hostname_A) is reachable from Server B ($hostname_B) over DNS" | tee -a ${LOG_FILE}
    if ssh -i /root/.ssh/id_rsa_prvsnr -o "StrictHostKeyChecking no" ${private_data_ip_node_2} "ping -c1 -W2  $hostname_A" > /dev/null; then
        # Ping is successfull, no need to add entry in /etc/hosts
        echo "Server A ($hostname_A) is reachable from ServerB ($hostname_B) over DNS" | tee -a ${LOG_FILE}
        _ping_status_B_to_A=true
    else
        # Ping failed, need to add entry in /etc/hosts
        echo "ERROR: Server A ($hostname_A) is not reachable from server B ($hostname_B) over DNS" |tee -a ${LOG_FILE}
        _ping_status_B_to_A=false
    fi

    # Steps to add entries in /etc/hosts
    # 1. Is mgmt_ip_A already added in /etc/hosts on node A?
    #     1.1 Yes: mgmt_ip_A is added in /etc/hosts
    #            Is the entry against hostname_A? 
    #              Yes: We are good, do nothing. 
    #              NO: Update the hostname against the mgmt_ip_A
    #     1.2 No: add the new entry in /etc/hosts for mgmt_ip_A
    # 2. Repeat for mgmt_ip_B on node A.
    # 3. Repeat 1 and 2 for node B


    # node A
    echo "Checking DNS entries in /etc/hosts on server A for management IP of server A (${mgmt_ip_A})" | tee -a ${LOG_FILE}
    # 1. Is mgmt_ip_A already added in /etc/hosts on node A?
    if grep -q "${mgmt_ip_A}" /etc/hosts ; then
        # 1.1 mgmt_ip_A is added in /etc/hosts
        if grep "${mgmt_ip_A}" /etc/hosts | grep "${hostname_A}"; then
            # mgmt_ip_A is added in /etc/hosts and is against hostname_A
            echo "Server A: /etc/hosts already has dns entry for management IP of server A (${mgmt_ip_A}) against hostname of Server A (${hostname_A})" | tee -a ${LOG_FILE}
        else
            # Entry for ${mgmt_ip_A} is there in /etc/hosts but it's not against hostname_A
            # Update the hostname against the existing entry.
            echo "Server A: Warning: /etc/hosts already has entry for management IP (${mgmt_ip_A}) of server A (${hostname_A}) but against wrong/old hostname" | tee -a  ${LOG_FILE}
            #TODO: Update the entry in /etc/hosts. Remove and add it?
        fi
    else
        # 1.2 /etc/hosts does not has the entry, add it
        echo "Server A: Adding entry in /etc/hosts for management IP (${mgmt_ip_A}) of server A ($hostname_A)" | tee -a  ${LOG_FILE}
        echo "$mgmt_ip_A $hostname_A" >> /etc/hosts
        echo "Done" | tee -a ${LOG_FILE}
    fi

    # 2. Is mgmt_ip_B already added in /etc/hosts on node A?
    echo "Checking DNS entries in /etc/hosts on server A for management IP of Server B (${mgmt_ip_B})" | tee -a ${LOG_FILE}
    if grep -q "${mgmt_ip_B}" /etc/hosts ; then
        # 2.1 mgmt_ip_B is added in /etc/hosts
        if grep "${mgmt_ip_B}" /etc/hosts | grep "${hostname_B}"; then
            # mgmt_ip_B is added in /etc/hosts and is against hostname_B
            echo "Server A: /etc/hosts already has dns entry for management IP of server B (${mgmt_ip_B}) against hostname of Server B (${hostname_B})" | tee -a ${LOG_FILE}
        else
            # Entry for ${mgmt_ip_B} is there in /etc/hosts but it's not against hostname_B
            # Update the hostname against the existing entry.
            echo "Server A: Warning: /etc/hosts already has entry for management IP (${mgmt_ip_B}) of server B (${hostname_B}) but against wrong/old hostname" | tee -a  ${LOG_FILE}
            #TODO: Update the entry in /etc/hosts. Remove and add it?
        fi
    else
        # 2.2 /etc/hosts does not has the entry, add it
        echo "Server A: Adding entry in /etc/hosts for management IP (${mgmt_ip_B}) of server B ($hostname_B)" | tee -a  ${LOG_FILE}
        echo "$mgmt_ip_B $hostname_B" >> /etc/hosts
        echo "Done" | tee -a ${LOG_FILE}
    fi

    # Repeat for node B
    echo "Checking DNS entries in /etc/hosts on server B for management IP of node A (${mgmt_ip_A})" | tee -a ${LOG_FILE}
    # 1. Is mgmt_ip_A already added in /etc/hosts on node B?
    if $ssh_cmd srvnode-2 'grep -q \"${mgmt_ip_A}\" /etc/hosts' ; then
        # 1.1 mgmt_ip_A is added in /etc/hosts
        if $ssh_cmd srvnode-2 'grep \"${mgmt_ip_A}\" /etc/hosts | grep \"${hostname_A}\"'; then
            # mgmt_ip_A is added in /etc/hosts and is against hostname_A
            echo "Server B: /etc/hosts already has dns entry for management IP  of server A (${mgmt_ip_A}) against hostname of Server A (${hostname_A})" | tee -a ${LOG_FILE}
        else
            # Entry for ${mgmt_ip_A} is there in /etc/hosts but it's not against hostname_A
            # Update the hostname against the existing entry.
            echo "Server B: Warning: /etc/hosts already has entry for management IP (${mgmt_ip_A}) of server A (${hostname_A}) but against wrong/old hostname" | tee -a  ${LOG_FILE}
            #TODO: Update the entry in /etc/hosts. Remove and add it?
        fi
    else
        # 1.2 /etc/hosts does not has the entry, add it
        echo "Server B: Adding entry in /etc/hosts for management IP (${mgmt_ip_A}) of server A ($hostname_A)" | tee -a  ${LOG_FILE}
        echo "$mgmt_ip_A $hostname_A" > /tmp/dns_a.tmp
        $scp_cmd /tmp/dns_a.tmp srvnode2:/tmp/dns_a.tmp
        $ssh_cmd srvnode-2 'cat /tmp/dns_a.tmp >> /etc/hosts' >> /etc/hosts
        echo "Done" | tee -a ${LOG_FILE}
    fi

    # Repeat for mgmtIP_B on node B
    echo "Checking DNS entries in /etc/hosts on server B for management IP of node B (${mgmt_ip_B})" | tee -a ${LOG_FILE}
    # 2. Is mgmt_ip_B already added in /etc/hosts on node B?
    if $ssh_cmd srvnode-2 'grep -q \"${mgmt_ip_B}\" /etc/hosts' ; then
        # 2.1 mgmt_ip_B is added in /etc/hosts
        if $ssh_cmd srvnode-2 'grep \"${mgmt_ip_B}\" /etc/hosts | grep \"${hostname_B}\"'; then
            # mgmt_ip_B is added in /etc/hosts and is against hostname_B
            echo "Server B: /etc/hosts already has dns entry for management IP  of server B (${mgmt_ip_B}) against hostname of Server B (${hostname_B})" | tee -a ${LOG_FILE}
        else
            # Entry for ${mgmt_ip_B} is there in /etc/hosts but it's not against hostname_B
            # Update the hostname against the existing entry.
            echo "Server B: Warning: /etc/hosts already has entry for management IP (${mgmt_ip_B}) of server B (${hostname_B}) but against wrong/old hostname" | tee -a  ${LOG_FILE}
            #TODO: Update the entry in /etc/hosts. Remove and add it?
        fi
    else
        # 2.2 /etc/hosts does not has the entry, add it
        echo "Server B: Adding entry in /etc/hosts for management IP (${mgmt_ip_B}) of server B ($hostname_B)" | tee -a  ${LOG_FILE}
        echo "$mgmt_ip_B $hostname_B" > /tmp/dns_b.tmp
        $scp_cmd /tmp/dns_b.tmp srvnode2:/tmp/dns_b.tmp
        $ssh_cmd srvnode-2 'cat /tmp/dns_b.tmp >> /etc/hosts' >> /etc/hosts
        echo "Done" | tee -a ${LOG_FILE}
    fi

}

ssh_config_update()
{
    # Replace Server A entry
    echo "Updating server A hostname (${hostname_A}) in ssh config file of server A" | tee -a ${LOG_FILE}
    local line_to_replace=$(grep -m1 -noP "HostName" /root/.ssh/config|tail -1|cut -d: -f1)
    sed -i "s|Host srvnode-1.*|Host srvnode-1 ${hostname_A}|" /root/.ssh/config
    sed -i "${line_to_replace}s|HostName.*|HostName ${hostname_A}|" /root/.ssh/config
    echo "Done" | tee -a ${LOG_FILE}

    # Replace Server B entry
    echo "Updating server B hostname (${hostname_B}) in ssh config file of server A" | tee -a ${LOG_FILE}
    local line_to_replace=$(grep -m2 -noP "HostName" /root/.ssh/config|tail -1|cut -d: -f1)
    sed -i "s|Host srvnode-2.*|Host srvnode-2 ${hostname_B}|" /root/.ssh/config
    sed -i "${line_to_replace}s|HostName.*|HostName ${hostname_B}|" /root/.ssh/config
    echo "Done" | tee -a ${LOG_FILE}

    echo "Copying the ssh config file from Server A to Server B" | tee -a ${LOG_FILE}
    $scp_cmd /root/.ssh/config srvnode-2:/root/.ssh/config
    echo "Done"
}

minion_config_update()
{

    local line_to_replace=$(grep -m1 -noP "master: " /etc/salt/minion|tail -1|cut -d: -f1)
    
    echo "Setting Salt master (${hostname_A}) on server A (${hostname_A})" | tee -a ${LOG_FILE}
    sed -i "${line_to_replace}s|^master:.*|master: ${hostname_A}|" /etc/salt/minion
    echo "Done" | tee -a ${LOG_FILE}

    echo "Setting Salt master (${hostname_A}) on server B (${hostname_B})" | tee -a ${LOG_FILE}
    #TODO: Should we just scp minion file from Server A to server B?
    $ssh_cmd ${private_data_ip_node_2} "sed -i \"${line_to_replace}s|^master:.*|master: ${hostname_A}|\" /etc/salt/minion"
    echo "Done" | tee -a ${LOG_FILE}
    
    # It's safe to restart service on both nodes
    echo "Restarting salt-minion on Server A" | tee -a ${LOG_FILE}
    systemctl restart salt-minion
    echo "Done" | tee -a ${LOG_FILE}

    echo "Restarting salt-minion on Server B" | tee -a ${LOG_FILE}
    $ssh_cmd ${private_data_ip_node_2} "systemctl restart salt-minion"
    echo "Done" | tee -a ${LOG_FILE}
    sleep 5

    # Check if salt '*' test.ping works
    echo "Waiting for minion on Server A to become ready" | tee -a ${LOG_FILE}
    try=1; max_tries=10
    until salt -t 1 srvnode-1 test.ping >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: minion srvnode-1 seems still not ready after $max_tries attempts." | tee -a ${LOG_FILE}
            exit 1
        fi
        echo -n "." | tee -a ${LOG_FILE}
        try=$(( $try + 1 ))
    done
    echo "Minion srvnode-1 started successfully" | tee -a ${LOG_FILE}

    echo "Waiting for minion on Server B to become ready" | tee -a ${LOG_FILE}
    try=1; max_tries=10
    until salt -t 1 srvnode-2 test.ping >/dev/null 2>&1
    do
        if [[ "$try" -gt "$max_tries" ]]; then
            echo "ERROR: minion srvnode-2 seems still not ready after $max_tries attempts." | tee -a ${LOG_FILE}
            exit 1
        fi
        echo -n "." | tee -a ${LOG_FILE}
        try=$(( $try + 1 ))
    done
    echo "Minion srvnode-2 started successfully" | tee -a ${LOG_FILE}
}

# 1. Run cleanup 
echo "Capturing output of `ip a` on Server A for analysis (if needed)" | tee -a ${LOG_FILE}
ip a | tee -a ${LOG_FILE}

echo "Capturing output of `ip a` on Server B for analysis (if needed)" | tee -a ${LOG_FILE}
$ssh_cmd ${private_data_ip_node_2} 'ip a' | tee -a ${LOG_FILE}

seagate_refs_cleanup

# 2. Check if the volumes are being listed on both the nodes - lsblk
luns_availability_check

#3. check if the hostname contains 'seagate.com', if yes, take input for new hostname
hostname_validate_get_set

#4 update hostnames in local dns (/etc/hosts)
dns_update_hostnames

#5 Update hostnames in ssh config files
ssh_config_update

#6. Update minion files on both the nodes to point master to server A hostname
minion_config_update

#10. Run unboxing script
#11. Update controller IPs in pillar


#TODO: Correct ssh_cmd targets
