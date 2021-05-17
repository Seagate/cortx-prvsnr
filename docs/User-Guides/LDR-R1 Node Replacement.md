# Replace Node


## **Section-1 Pre-Requisits**  
**IMPORTANT PRE-CONDITIONs** - Before we start node replacement:  
* [ ] Make sure that cluster is properly deployed - check pcs status, hctl status  
* [ ] All services are Up and running fine.  
* [ ] I/Os are started from client.  
* [ ] Verify config.ini is correct.  
* [ ] CSM preboarding & onboarding process is completed.  
* [ ] Health view page is visible to user.  

1.  In case failover has not already happened, recover cluster on **Live Node** to enable a healthy fail-over:  
    ```
    pcs resouce cleanup --all
    ```  
    **NOTE**: This might take time. It is advisable to wait upto 15 minutes.
1.  Make all required connections from replacement node to the storage enclosure and to the live node.  
    Ensure the cabling is as per the designed specifications.
1.  Power-up the replacement node for reimage/ installation of OS
1.  Install OS on the replacement node
    * Obtain CORTX OS ISO image from Seagate Support
    * Using your favorite program, create USB stick with the content of this ISO. For example, on Linux you can run:
    ```
    dd if=cortx-os-1.0.0-<version>.iso of=/dev/<usb_disk> bs=1m
    ```
    (replace `<version>` and `<usb_disk>` with the correct values)
    * Boot the server from USB stick. The installation will start automatically, no user input is required.
1.  Assign a root password to the new node
1.  Adjust network settings
    * If using IP addresses provided via DHCP, update MAC addresses for the Management, BMC, and Public Data NICs on the DHCP server
    * If using IP addresses provided via DHCP, update `/etc/resolv.conf`. Run:
    ```
    dhclient <mgmt_nic>
    ```
    where:
 
    <mgmt_nic> is the name of the Management NIC (e.g., `eno1`)

    * If using static IP addresses, manually edit the respective `/etc/sysconfig/network-scripts/ifcfg-<interface>` for the Management and Public Data NICs and set correct IP addresses and netmasks. You can use the following template:
    ```
    DEVICE="<interface_name>"
    USERCTL="no"
    TYPE="Ethernet"
    BOOTPROTO="none"
    ONBOOT="yes"
    IPADDR="<ip_address>"
    NETMASK="<subnet_mask>"
    DEFROUTE="<route>"
    MTU="<mtu>"
    NM_CONTROLLED="no"
    ZONE=<firewall_zone>
    ```
 
    where:

    <interface_name> - the name of the interface (e.g., `eno1`, `enp175s0f0`, etc.)

    <ip_address> - IP address

    <subnet_mask> - subnet mask

    <route> - set to "yes" for Management NIC, set to "no" for Public Data NIC

    <mtu> - set to "1500" for Management NIC, set to "9000" for Public Data NIC

    <firewall_zone> - set to "public" for Management NIC, set to "public-data-zone" for Public Data NIC

    * If static IP addresses are used, BMC interface should be configured manually using BMC WebUI console or `ipmitool`. Example of using `ipmitool`:
    ```
    ipmitool lan set 1 ipsrc static
    ipmitool lan set 1 ipaddr <BMC_ip_address>
    ipmitool lan set 1 netmask <BMC_subnet_mask>
    ipmitool lan set 1 defgw ipaddr <BMC_gateway>
    ipmitool lan set 1 arp respond on
    ```
    
    where:

    <BMC_ip_address> - IP address of the BMC interface

    <BMC_subnet_mask> - Subnet mask of the BMC interface

    <BMC_gateway> - gateway information for BMC interface

    It's recommended to verify basic network connectivity (e.g., ping) for each interface before continuing. 

1.  Follow this checklist:  
    * [ ] Check if the following values on new node are same as values on old node  
          If values are NOT same, we need to manually configure them.  
        * [ ] BMC IP  
        * [ ] BMC username  
        * [ ] BMC password  
        * [ ] Hostname  
          If required, set hostname on replaced node using command: `hostnamectl set-hostname <old-Node's-hostname>`  
        * [ ] Management network IP  
          If management network IP is not the same, then get help from your network team to ensure the new (replacement node) is assigned the same IP for management network, as the old node being replaced  
        * [ ] Make sure that you are able to access the replaced node with old node's hostname  
        
    * [ ] Ensure the LUNs are mapped and available on replaced node
        * [ ] Execute command: `rescan-scsi-bus.sh` **NOTE: This needs to be done on new node only**  
        * [ ] Execute Comamnd: `lsblk -S|grep sas`  
        * [ ] Ensure same number of disks are seen in output of above command on both nodes  
        * [ ] If the LUNs are absent, try mapping any unmapped disk volumes (Refer CLI docs for volume mappings)  
              **NOTE**: Do not remove or remap any existing LUNs
    * [ ] Check if SWAP volumes are available on replaced node after reimage  
        Run command:  
        `lvdisplay | grep -e "LV Path" | grep -e 'lv_main_swap'`  
        Reference Output:  
        ```  
        LV Path                /dev/vg_metadata_srvnode-1/lv_main_swap              
        LV Path                /dev/vg_metadata_srvnode-2/lv_main_swap  
        ```  
    * [ ] Check if raw metadata volumes are available on replaced node after reimage  
        Run Command:  
        `lvdisplay | grep -e "LV Path" | grep -e 'lv_raw_metadata'`  
        Reference Output:  
        ```  
         LV Path                /dev/vg_metadata_srvnode-2/lv_raw_metadata  
         LV Path                /dev/vg_metadata_srvnode-1/lv_raw_metadata
        ```  
    **NOTE**: If these lv partitions are not found try:  
    1. Command: `rescan-scsi-bus.sh`  
    1. Reboot the node  
1.  Check for Mellanox drivers are installed on replacement node:
    ```
    $ rpm -qa|grep mlnx
    libibverbs-41mlnx1-OFED.4.7.0.0.2.47329.x86_64
    libmlx5-41mlnx1-OFED.4.7.0.3.3.47329.x86_64
    libmlx4-41mlnx1-OFED.4.7.3.0.3.47329.x86_64
    ibsim-0.7mlnx1-0.11.g85c342b.47329.x86_64
    mlnx-ofa_kernel-4.7-OFED.4.7.3.2.9.1.g457f064.rhel7u7.x86_64
    kmod-knem-1.1.3.90mlnx1-OFED.4.7.2.0.7.1.gec1f2f8.rhel7u7.x86_64
    kmod-kernel-mft-mlnx-4.13.3-1.rhel7u7.x86_64
    mlnx-fw-updater-4.7-3.2.9.0.x86_64
    dapl-2.1.10mlnx-OFED.3.4.2.1.0.47329.x86_64
    libibverbs-devel-41mlnx1-OFED.4.7.0.0.2.47329.x86_64
    librxe-41mlnx1-OFED.4.4.2.4.6.47329.x86_64
    librxe-devel-static-41mlnx1-OFED.4.4.2.4.6.47329.x86_64
    librdmacm-devel-41mlnx1-OFED.4.7.3.0.6.47329.x86_64
    dapl-devel-2.1.10mlnx-OFED.3.4.2.1.0.47329.x86_64
    libmlx5-devel-41mlnx1-OFED.4.7.0.3.3.47329.x86_64
    ibacm-41mlnx1-OFED.4.3.3.0.0.47329.x86_64
    libibverbs-devel-static-41mlnx1-OFED.4.7.0.0.2.47329.x86_64
    kmod-mlnx-ofa_kernel-4.7-OFED.4.7.3.2.9.1.g457f064.rhel7u7.x86_64
    mlnx-ofa_kernel-devel-4.7-OFED.4.7.3.2.9.1.g457f064.rhel7u7.x86_64
    knem-1.1.3.90mlnx1-OFED.4.7.2.0.7.1.gec1f2f8.rhel7u7.x86_64
    librdmacm-41mlnx1-OFED.4.7.3.0.6.47329.x86_64
    libibcm-41mlnx1-OFED.4.1.0.1.0.47329.x86_64
    libmlx4-devel-41mlnx1-OFED.4.7.3.0.3.47329.x86_64
    libibcm-devel-41mlnx1-OFED.4.1.0.1.0.47329.x86_64
    dapl-utils-2.1.10mlnx-OFED.3.4.2.1.0.47329.x86_64
    librdmacm-utils-41mlnx1-OFED.4.7.3.0.6.47329.x86_64
    srptools-41mlnx1-5.47329.x86_64
    libibverbs-utils-41mlnx1-OFED.4.7.0.0.2.47329.x86_64
    mlnx-ethtool-5.1-1.47329.x86_64
    dapl-devel-static-2.1.10mlnx-OFED.3.4.2.1.0.47329.x86_64
    mlnx-iproute2-5.2.0-1.47329.x86_64
    mlnx-ofed-all-4.7-3.2.9.0.rhel7.7.noarch
    ```


## **Section-2 Replacement Process**

**NOTE**: All the below steps need to be executed on Healthy Node.

1.  Copy /etc/hosts file to replacement node from healthy node:
    ```
    scp -F /dev/null -r /etc/hosts <target_node_fqdn>:/etc/hosts
    ```

1.  On successful reboot after cortx-prereq step, copy key to replacement node from healthy node:
    ```
    scp -F /dev/null -r /root/.ssh/* <target_node_fqdn>:/root/.ssh/
    ```

1.  Stop Management VIP before proceeding:  
    ```
    pcs resource disable kibana-vip --force
    ```  
    Wait for resource to stop: `pcs status|grep kibana-vip`  
    `kibana-vip (ocf::heartbeat:IPaddr2):       Stopped (disabled)`  

1.  Bootstrap provisioner
    * **Replacing secondary node**  
      ```
      provisioner replace_node --node-id srvnode-2 --logfile --logfile-filename /var/log/seagate/provisioner/replace_node.log
      ```  
      **OR**  
    * **Replacing primary node**  
      ```
      provisioner replace_node --node-id srvnode-1 --logfile --logfile-filename /var/log/seagate/provisioner/replace_node.log
      ```  

1.  Test success of bootstrap from live node:  
    ```
    salt '*' test.ping
    ```

1.  For `--source local` deployment in factory scenario, execute following command before deploy-replacement:  
    ```
    ln -s /usr/local/bin/provisioner /usr/bin/provisioner
    ```

1.  Re-enable the management VIP:  
    ```
    pcs resource enable kibana-vip --force
    ```
    Wait for resource to start: `pcs status|grep kibana-vip`  
    `kibana-vip (ocf::heartbeat:IPaddr2):       started `  

1.  Execute following command on healthy node.  
    If healthy node is srvnode-1, then execute on srvnode-1  
    **Healthy node**: srvnode-1  
    **Replaced node**: srvnode-2  
    ```
    /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -Ssrvnode-2
    ```  
    **OR**  
    If healthy node is srvnode-2, then execute on srvnode-2  
    **Healthy node**: srvnode-2  
    **Replaced node**: srvnode-1  
    ```
    /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -Ssrvnode-1
    ```  
    This would be **stage one**, which would cover:  
    1.  Setup multipath on replacement node from srvnode-1 (live node) 
        ```
        salt srvnode-2/1 state.apply components.system.storage.multipath.prepare
        salt srvnode-2/1 state.apply components.system.storage.multipath.install
        salt srvnode-2/1 state.apply components.system.storage.multipath.config
        ```
    1.  Reboot the replacement node (srvnode-2):
        ```
        salt srvnode-2/1 system.reboot
        ```
1.  Wait for node to come up  
    1.  Ping test: `ping <replacement_node_fqdn>`  
    1.  SSH online test: `ssh <id_of_replacement_node> "exit"`  
    1.  Salt online test:  
        ```
        $ salt "*" test.ping  
        srvnode-2:
            True
        srvnode-1:
            True
        ```  

1.  On replaced node, check if the `salt-master` service has started.  
    ```
    ssh <target_node> "systemctl status salt-master"  
    ```
    If the `salt-master` service is seen as failed, execute the following commands by connecting to replaced node over ssh:
    ```
    $ systemctl stop salt-master salt-minion
    $ umount $(mount -l | grep gluster | cut -d ' ' -f3)
    $ systemctl restart glusterd
    $ systemctl restart glusterfsd
    $ systemctl start glusterfssharedstorage
    $ systemctl start salt-master salt-minion
    ```
    Check, if salt-master and salt-minion services are up and online:
    ```
    $ systemctl status salt-master salt-minion
    ```

1.  If the original setup was in-band consider setting up inband (skip for out-of-band)  
    ```
    salt "*" state.apply components.system.inband
    ```  

1.  Again from healthy node, execute `deploy-replacement` script for replacement node.  
    If healthy node is srvnode-1, then execute on srvnode-1
    **Healthy node**: srvnode-1  
    **Replaced node**: srvnode-2  
    ```
    /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -Ssrvnode-2
    ```  
    **OR**  
    If healthy node is srvnode-2, then execute on srvnode-2
    **Healthy node**: srvnode-2  
    **Replaced node**: srvnode-1  
    ```  
    /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -Ssrvnode-1
    ```  
    This would be **stage two**, which would cover the rest of the process  
1.  Wait for process to complete
1.  Once the process is complete check the HA status and ensure all services are started on respective nodes:
    ```
    pcs status
    ```

### Manual Commands  
In case of issues during the deploy-replacement script and there is a need to continue manually  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --removenode-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --system-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --prereq-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --iopath-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --ctrlpath-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --sync-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --ha-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --restore-states  
1.  /opt/seagate/cortx/provisioner/cli/replace_node/deploy-replacement -S<srvnode-id> --addnode-states  
1.  Recover **CSM Admin user**  
    ```
    . /opt/seagate/cortx/provisioner/cli/common_utils/utility_scripts.sh
    ensure_healthy_cluster
    python3 /opt/seagate/cortx/provisioner/cli/csm_admin_user.py -c /usr/bin/consul -n <srvnode-id> --syncpass  
    ```

## Consider Cleaning-up  
Reset replacement node flag, if everything looks ok:  
`provisioner pillar_set cluster/replace_node/minion_id \"\"`  

## Troubleshooting Guide
### Issue: RabbitMQ fails to add node to cluster  
If there's an issue with SSPL service startup and the issue turns out to be the following in RabbitMQ:  
```
$ systemctl status rabbitmq-server -l | grep "inconsistent_cluster,"
{"init terminating in do_boot",{rabbit,failure_during_boot,{error,{inconsistent_cluster,"Node 'rabbit@srvnode-2' thinks it's clustered with node 'rabbit@srvnode-1', but 'rabbit@srvnode-1' disagrees"}}}}
```
**Solution**:  
Follow these steps to reset rabbitmq-server cluster:
```
hctl node maintenance --all
salt "*" service.stop rabbitmq-server
salt "*" cmd.run "rm -rf /var/lib/rabbitmq/mnesia/*"
salt "*" service.start rabbitmq-server
salt "srvnode-1" cmd.run "rabbitmqctl start_app"
salt "srvnode-1" cmd.run "rabbitmqctl set_cluster_name rabbitmq-cluster"
salt "srvnode-2" cmd.run "rabbitmqctl stop_app"
salt "srvnode-2" cmd.run "rabbitmqctl join_cluster rabbit@srvnode-1"
salt "srvnode-2" cmd.run "rabbitmqctl start_app"
hctl node unmaintenance --all
```

# Cases To Be Considered
*  The data integrity has to be ensured  
*  It has to be ensured that the HA cluster has failed over and all the services are healthy after fail-over  
*  In case, something fails during fail-over the deploy-replacement, there should be clear demarcated stages to help isolate what has broken  
*  What happens of user hit's **CTRL+C**?
*  What happens, if srvnode-1 reboots during the replacement process?
