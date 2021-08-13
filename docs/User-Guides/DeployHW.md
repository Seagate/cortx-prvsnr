# Deploy HW: Local ISO Method [Draft: Awaiting validation]

## Provisioner CLI Commands for Single and Multi-node HW

# Before You Start  
Checklist:  
-  [x]  For single-node VM deployment, ensure the HW(s) is/are accessible over ssh.  
-  [x]  Do you see the devices on execution of this command:  
        ```  
        $ lsblk -S|grep SEAGATE|wc -l
        ```  
        If the expect number of devices is not found, execute the following commands and retry:
        ```  
        $ rescan-scsi-bus.sh
        ```  
-  [x]  Does your setup have valid hostnames, are the hostnames accessible:  
        ```  
        $ ping <hostname>
        ```  
-  [x]  Do you have IPs' assigned to all NICs?  
    ```  
    $ ip a  
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000  
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00  
        inet 127.0.0.1/8 scope host lo  
        valid_lft forever preferred_lft forever  
        inet6 ::1/128 scope host  
        valid_lft forever preferred_lft forever  
    2: eno1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000  
        link/ether ac:1f:6b:c8:91:ec brd ff:ff:ff:ff:ff:ff  
        inet 10.xxx.yyy.zzz/20 brd 10.xxx.255.255 scope global noprefixroute dynamic eno1  
        valid_lft 342949sec preferred_lft 342949sec  
        inet6 fe80::ae1f:6bff:fec8:91ec/64 scope link  
        valid_lft forever preferred_lft forever  
    3: enp175s0f0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP group default qlen 1000  
        link/ether 98:03:9b:06:a6:4c brd ff:ff:ff:ff:ff:ff  
        inet 192.168.lll.mmm/19 brd 192.168.nnn.255 scope global dynamic enp175s0f0  
        valid_lft 27277sec preferred_lft 27277sec  
        inet6 fe80::9a03:9bff:fe06:a64c/64 scope link  
        valid_lft forever preferred_lft forever  
    4: enp175s0f1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP group default qlen 1000  
        link/ether 98:03:9b:06:a6:4d brd ff:ff:ff:ff:ff:ff  
        inet 192.168.ooo.ppp/19 brd 192.168.qqq.255 scope global dynamic enp175s0f1  
        valid_lft 32354sec preferred_lft 32354sec  
        inet6 fe80::9a03:9bff:fe06:a64d/64 scope link  
        valid_lft forever preferred_lft forever  
    5: eno2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000  
        link/ether ac:1f:6b:c8:91:ed brd ff:ff:ff:ff:ff:ff  
    6: tap0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 1000  
        link/ether c2:01:e2:4e:b9:27 brd ff:ff:ff:ff:ff:ff  
        inet 10.0.0.4/24 scope global tap0  
        valid_lft forever preferred_lft forever  
        inet6 fe80::c001:e2ff:fe4e:b927/64 scope link  
        valid_lft forever preferred_lft forever  
    ```  
-  [x]  Identify primary node and run below commands on primary node  
    **NOTE**: For single-node, the node itself is treated as primary node.  

# HW Preparation for Deployment
1.  Set root user password on all nodes:
    ```  
    sudo passwd root
    ```
1.  Download ISOs and shell-scripts  
    **NOTE**: Contact Cortx RE team for latest ISO.  
    ```
    mkdir /opt/isos
    ```

    **NOTE**: If you are outside Seagate corporate network, download these files manually to `/opt/isos` directory and skip to **Prepare cortx-prvsnr API** step.  
    Get details for ISO download URL from Cortx RE team. The URL should have the following files:  
    * cortx-2.0.0-*-single.iso
    * cortx-os-1.0.0-*.iso or centos-7.8-minimal.iso
    * cortx-prep.sh 

    ```
    # Set source URL
    # It should have the following: cortx-2.0.0-*-single.iso, cortx-os-2.0.0-*.iso
    CORTX_RELEASE_REPO=<URL to Cortx ISO hosting>

    # Download Single ISO
    pushd /opt/isos
    SINGLE_ISO=$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's/<\/*[^>]*>//g' | cut -f1 -d' ' | grep 'single.iso')
    curl -O ${CORTX_RELEASE_REPO}/iso/${SINGLE_ISO}
    
    # Download OS ISO
    OS_ISO=$(curl -s ${CORTX_RELEASE_REPO}/iso/ | sed 's/<\/*[^>]*>//g' | cut -f1 -d' '|grep  "cortx-os")
    curl -O ${CORTX_RELEASE_REPO}/iso/${OS_ISO}
    
    # Download cortx_prep script
    curl -O https://raw.githubusercontent.com/Seagate/cortx-prvsnr/stable/cli/src/cortx_prep.sh
    popd    
    ```
1.  Prepare cortx-prvsnr API
    ```
    pushd /opt/isos
    # Execute cortx-prep script
    chmod +x /opt/isos/cortx-prep.sh
    sh /opt/isos/cortx-prep.sh
    popd
    ```
1.  Verify provisioner version (0.36.0 and above)
    ```
    provisioner --version
    ```

1.  Identify storage volumes:
    ```
    cp /usr/share/doc/device-mapper-multipath-0.4.9/multipath.conf /etc/multipath.conf
    systemctl restart multipathd
    device_list=$(multipath -ll|grep mpath|sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g'|paste -s -d, -)
    # Metadata device
    echo ${device_list%%,*}
    # Data device
    echo ${device_list#*,}
    ```

1.  Create config.ini file to some location:  
    **IMPORTANT NOTE: Please check every details in this file correctly according to your node.**  
    **Verify interface names are correct as per your node**  

    Update required details in `~/config.ini` use sample config.ini  
    Use storage volumes from commands above to fill in values for **_storage.cvg.0.data_devices_** and **_storage.cvg.0.data_devices_**  
    ```  
    vi ~/config.ini
    ```  
    
    ## Sample config.ini for single node HW  
    ```
    [cluster]
    cluster_ip=
    mgmt_vip=

    [srvnode_default]
    network.data.private_interfaces=enp175s0f1
    network.data.public_interfaces=enp175s0f0
    network.mgmt.interfaces=eno1
    bmc.user=ADMIN
    bmc.secret=bmcADMIN!
    storage.cvg.0.data_devices=/dev/disk/by-id/dm-name-mpathc,/dev/disk/by-id/dm-name-mpathd,/dev/disk/by-id/dm-name-mpathe,/dev/disk/by-id/dm-name-mpathf,/dev/disk/by-id/dm-name-mpathg,/dev/disk/by-id/dm-name-mpathh,/dev/disk/by-id/dm-name-mpathi,/dev/disk/by-id/dm-name-mpathj,/dev/disk/by-id/dm-name-mpathk
    storage.cvg.0.metadata_devices=/dev/disk/by-id/dm-name-mpathb

    [srvnode-1]
    hostname=srvnode-1.localdomain
    roles=primary,openldap_server

    [enclosure_default]
    type=RBOD
    controller.primary.ip=10.0.0.2
    controller.secondary.ip=10.0.0.3
    controller.user=manage
    controller.secret=

    [enclosure-1]
    ```

    ## Sample config.ini for 3 node HW
    ```
    [cluster]
    cluster_ip=
    mgmt_vip=

    [srvnode_default]
    network.data.private_interfaces=enp175s0f1
    network.data.public_interfaces=enp175s0f0
    network.mgmt.interfaces=eno1
    bmc.user=ADMIN
    bmc.secret=bmcADMIN!

    [srvnode-1]
    hostname=srvnode-1.localdomain
    roles=primary,openldap_server
    storage.cvg.0.data_devices=/dev/disk/by-id/dm-name-mpathc,/dev/disk/by-id/dm-name-mpathd,/dev/disk/by-id/dm-name-mpathe,/dev/disk/by-id/dm-name-mpathf,/dev/disk/by-id/dm-name-mpathg,/dev/disk/by-id/dm-name-mpathh,/dev/disk/by-id/dm-name-mpathi,/dev/disk/by-id/dm-name-mpathj,/dev/disk/by-id/dm-name-mpathk
    storage.cvg.0.metadata_devices=/dev/disk/by-id/dm-name-mpathb

    [srvnode-2]
    hostname=srvnode-2.localdomain
    roles=primary,openldap_server
    storage.cvg.0.data_devices=/dev/disk/by-id/dm-name-mpathc,/dev/disk/by-id/dm-name-mpathd,/dev/disk/by-id/dm-name-mpathe,/dev/disk/by-id/dm-name-mpathf,/dev/disk/by-id/dm-name-mpathg,/dev/disk/by-id/dm-name-mpathh,/dev/disk/by-id/dm-name-mpathi,/dev/disk/by-id/dm-name-mpathj,/dev/disk/by-id/dm-name-mpathk
    storage.cvg.0.metadata_devices=/dev/disk/by-id/dm-name-mpathb

    [srvnode-3]
    hostname=srvnode-3.localdomain
    roles=primary,openldap_server
    storage.cvg.0.data_devices=/dev/disk/by-id/dm-name-mpathc,/dev/disk/by-id/dm-name-mpathd,/dev/disk/by-id/dm-name-mpathe,/dev/disk/by-id/dm-name-mpathf,/dev/disk/by-id/dm-name-mpathg,/dev/disk/by-id/dm-name-mpathh,/dev/disk/by-id/dm-name-mpathi,/dev/disk/by-id/dm-name-mpathj,/dev/disk/by-id/dm-name-mpathk
    storage.cvg.0.metadata_devices=/dev/disk/by-id/dm-name-mpathb

    [enclosure_default]
    type=RBOD
    controller.primary.ip=10.0.0.2
    controller.secondary.ip=10.0.0.3
    controller.user=manage
    controller.secret=

    [enclosure-1]

    [enclosure-2]

    [enclosure-3]
    ```
    **NOTE** : `private_ip, bmc_secret, bmc_user ` should be None for VM.


# Deploy HW Manually:

Manual deployment of HW consists of following steps from Auto-Deploy, which could be individually executed:  
**NOTE**: Ensure [VM Preparation for Deployment](#vm-preparation-for-deployment) has been addressed successfully before proceeding  

1.  **Bootstrap HW(s)**: Run setup_provisioner provisioner cli command:
    
    NOTE: Run this command as part of temporary HW patch:  
    ```
    sed -i "s|'components.system.storage.enclosure_id',|#'components.system.storage.enclosure_id',|g" /usr/lib/python3.6/site-packages/provisioner/commands/setup_provisioner.py
    ```

    ## Single Node HW: Bootstrap
    **If using remote hosted repos**:  
    ```
    provisioner setup_provisioner \
        --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
        --source iso --config-path ~/config.ini \
        --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
        srvnode-1:$(hostname -f)
    ```

    ## Multi Node HW: Bootstrap
    **If using remote hosted repos**:  
    ```
    provisioner setup_provisioner  \
        --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
        --ha --source iso --config-path ~/config.ini \
        --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
        srvnode-1:<fqdn:primary_hostname> \
        srvnode-2:<fqdn:secondary_hostname> \
        srvnode-3:<fqdn:secondary_hostname>
    ```
    Example:
    ```
    provisioner setup_provisioner \
            --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
            --ha --source iso --config-path ~/config.ini \
            --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
            srvnode-1:host1.localdomain srvnode-2:host2.localdomain srvnode-3:host3.localdomain
    ```

    **NOTE**:  
    1.  This command will ask for each node's **root password** during initial cluster setup.  
    This is one time activity required to setup passwordless ssh across nodes.  

1.  Update pillar and export pillar data for confstore:  
    ```
    provisioner configure_setup /root/config.ini <number of nodes in cluster>
    salt-call state.apply components.system.config.pillar_encrypt
    salt-call state.apply components.system.storage.enclosure_id
    salt-call state.apply components.system.config.sync_salt
    salt-call state.apply components.provisioner.config.generate_cluster_pillar
    provisioner confstore_export
    ```


1.  Bootstrap Validation
    Once deployment is bootstrapped (auto_deploy or setup_provisioner) command is executed successfully, verify salt master setup on both nodes (setup verification checklist)
    ```
    salt '*' test.ping  
    salt "*" service.stop puppet
    salt "*" service.disable puppet
    salt '*' pillar.get release  
    salt '*' grains.get node_id  
    salt '*' grains.get machine_id  
    salt '*' grains.get enclosure_id  
    salt '*' grains.get roles  
    ``` 

1.  Deployment Based On Component Groups:  
    If provisioner setup is completed and you want to deploy in stages based on component group

    **NOTE**: At any stage, if there is a failure, it is advised to run destroy for that particular group.
    For help on destroy commands, refer to https://github.com/Seagate/cortx-prvsnr/wiki/Teardown-Node(s)#targeted-teardown

    ### Non-Cortx Group: System & 3rd-Party Softwares
    1.  System component group  
        **Single Node**
        ```sh
        provisioner deploy --setup-type single --states system
        ```
        **Multi Node**
        ```sh
        provisioner deploy --states system
        ```

    1.  Prereq component group  
        **Single Node**
        ```sh
        provisioner deploy --setup-type single --states prereq
        ```
        **Multi Node**
        ```sh
        provisioner deploy --states prereq
        ```

    
    ### Cortx Group: Utils
    1.  Utils component 
        **Single Node**  
        ```sh
        provisioner deploy --setup-type single --states utils
        ```
        **Multi Node**  
        ```sh
        provisioner deploy --setup-type 3_node --states utils
        ```

    ### Cortx Group: IO Path
    1.  IO path component group  
        **Single Node**  
        ```sh
        provisioner deploy --setup-type single --states iopath
        ```
        **Multi Node**  
        ```sh
        provisioner deploy --states iopath
        ```
    ### Cortx Group: Control Path
    1.  Control path component group  
        **Single Node**  
        ```sh
        provisioner deploy --setup-type single --states controlpath
        ```
        **Multi Node**  
        ```sh
        provisioner deploy --states controlpath
        ```

    ### Cortx Group: HA Path
    1.  Ha path component group  
        **Single Node**  
        ```sh
        provisioner deploy --setup-type single --states ha
        ```
        **Multi Node**  
        ```sh
        provisioner deploy --states ha
        ```

    ### Start Cluster (irrespective of number of nodes):  
    1.  Execute the following command on primary node to start the cluster:
        ```sh
        cortx cluster start
        ```

    1.  Verify Cortx cluster status:  
        ```sh
        hctl status
        ```
