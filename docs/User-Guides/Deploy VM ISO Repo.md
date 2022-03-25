# Deploy VM: ISO Repo Method
## Provisioner CLI Commands for Single and Multi-node VM

`auto_deploy_vm` CLI command will setup Salt, Provisioner and deploy all components.

Salt configuration will have multi-master support to recover/replace a node, if failed. 


# Before You Start  
Checklist:  
-  [x]  For Single Node VM Deployment, ensure the VM is created with exactly 2 attached disks.  
-  [x]  Do you see the devices on execution of this command: lsblk ?  
-  [x]  Do both the systems on your setup have valid hostnames, are the hostnames accessible: ping <hostname>?  
-  [x]  Do you have IPs' assigned to all NICs eth0, eth1 and eth2?  
-  [x]  Identify primary node and run below commands on primary node  
    **NOTE**: For single-node VM, the VM node itself is treated as primary node.  

# VM Preparation for Deployment
1.  Set root user password on all nodes:
    ```  
    sudo passwd root
    ```
1.  Refresh the machine_id on VM:  
    ```
    rm /etc/machine-id
    systemd-machine-id-setup
    cat /etc/machine-id
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
    * cortx-prep-2.0.0-*.sh or download https://github.com/Seagate/cortx-prvsnr/blob/stable/cli/src/cortx_prep.sh

    ```
    # Set source URL
    # It should have the following: cortx-2.0.0-*-single.iso, cortx-os-1.0.0-*.iso, cortx-prep-2.0.0-*.sh
    CORTX_RELEASE_REPO=<URL to Cortx ISO hosting>

    # Download Single ISO
    pushd /opt/isos
    SINGLE_ISO=$(curl -s ${CORTX_RELEASE_REPO} | sed 's/<\/*[^>]*>//g' | cut -f1 -d' ' | grep 'single.iso')
    curl -O ${CORTX_RELEASE_REPO}/iso/${SINGLE_ISO}
    # Download OS ISO
    OS_ISO=$(curl -s ${CORTX_RELEASE_REPO} | sed 's/<\/*[^>]*>//g' | cut -f1 -d' '|grep  "cortx-os")
    curl -O ${CORTX_RELEASE_REPO}/iso/${OS_ISO}
    # Download cortx_prep script
    CORTX_PREP=$(curl -s ${CORTX_RELEASE_REPO} | sed 's/<\/*[^>]*>//g' | cut -f1 -d' '|grep  ".sh")
    curl -O ${CORTX_RELEASE_REPO}/iso/${CORTX_PREP}
    popd    
    ```
1.  Prepare cortx-prvsnr API
    ```
    pushd /opt/isos
    # Run cortx-prep script
    sh /opt/isos/cortx-prep*.sh
    popd
    ```
1.  Verify provisioner version (0.36.0 and above)
    ```
    provisioner --version
    ```

1.  Create config.ini file to some location:   
    **IMPORTANT NOTE: Please check every details in this file correctly according to your node.**  
    **Verify interface names are correct as per your node**  

    Update required details in `~/config.ini` use sample config.ini 
    ```
    vi ~/config.ini
    ```
    
    ## Sample config.ini for single node VM
    ```
    [srvnode_default]
    network.data.private_interfaces=eth3,eth4
    network.data.public_interfaces=eth1,eth2
    network.mgmt.interfaces=eth0
    bmc.user=None
    bmc.secret=None
    storage.cvg.0.data_devices=/dev/sdc
    storage.cvg.0.metadata_devices=/dev/sdb
    network.data.private_ip=None

    [srvnode-1]
    hostname=srvnode-1.localdomain
    roles=primary,openldap_server

    [enclosure_default]
    type=virtual

    [enclosure-1]
    ```

    ## Sample config.ini for 3 node VM
    ```
    [srvnode_default]
    network.data.private_interfaces=eth3,eth4
    network.data.public_interfaces=eth1,eth2
    network.mgmt.interfaces=eth0
    bmc.user=None
    bmc.secret=None
    storage.cvg.0.data_devices=/dev/sdc,/dev/sdd
    storage.cvg.0.metadata_devices=/dev/sdb
    network.data.private_ip=None

    [srvnode-1]
    hostname=srvnode-1.localdomain
    roles=primary,openldap_server

    [srvnode-2]
    hostname=srvnode-2.localdomain
    roles=primary,openldap_server

    [srvnode-3]
    hostname=srvnode-3.localdomain
    roles=primary,openldap_server

    [enclosure_default]
    type=virtual

    [enclosure-1]

    [enclosure-2]

    [enclosure-3]
    ```
    **NOTE** : `private_ip, bmc_secret, bmc_user ` should be None for VM.


# Deploy VM Manually:

Manual deployment of VM consists of following steps from Auto-Deploy, which could be individually run:  
**NOTE**: Ensure [VM Preparation for Deployment](#vm-preparation-for-deployment) has been addressed successfully before proceeding  

1.  **Bootstrap VM(s)**: Run setup_provisioner provisioner cli command:
    
    ## Single Node VM: Bootstrap
    **If using remote hosted repos**:  
    ```
    provisioner setup_provisioner \
        --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
        --source iso --config-path ~/config.ini \
        --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
        srvnode-1:$(hostname -f)
    ```

    ## Multi Node VM: Bootstrap
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
    1.  [OPTIONAL] For setting up a cluster of more than 3 nodes do append `--name <setup_profile_name>` to auto_deploy_vm command input parameters. 

1.  Update pillar and export pillar data for confstore:  
    ```
    provisioner configure_setup /root/config.ini 1
    salt-call state.apply components.system.config.pillar_encrypt
    provisioner confstore_export
    ```


1.  Bootstrap Validation
    Once deployment is bootstrapped (auto_deploy or setup_provisioner) command is run successfully, verify salt-master setup on both nodes (setup verification checklist)
    ```
    salt '*' test.ping  
    salt "*" service.stop puppet
    salt "*" service.disable puppet
    salt '*' pillar.get release  
    salt '*' grains.get node_id  
    salt '*' grains.get cluster_id  
    salt '*' grains.get roles  
    ``` 

1.  Deployment Based On Component Groups:  
    If provisioner setup is completed and you want to deploy in stages based on component group

    ### Non-Cortx Group: System & 3rd-Party Softwares
    1.  System component group  
        **Single Node**
        ```
        provisioner deploy_vm --setup-type single --states system
        ```
        **Multi Node**
        ```
        provisioner deploy_vm --states system
        ```
    1.  Prereq component group  
        **Single Node**
        ```
        provisioner deploy_vm --setup-type single --states prereq
        ```
        **Multi Node**
        ```
        provisioner deploy_vm --states prereq
        ```

    ### Cortx Group: IO Path
    1.  IO path component group  
        **Single Node**  
        ```
        provisioner deploy_vm --setup-type single --states iopath
        ```
        **Multi Node**  
        ```
        provisioner deploy_vm --states iopath
        ```
    ### Cortx Group: Control Path
    1.  Control path component group  
        **Single Node**  
        ```
        provisioner deploy_vm --setup-type single --states controlpath
        ```
        **Multi Node**  
        ```
        provisioner deploy_vm --states controlpath
        ```

    ### Start Cluster (irrespective of number of nodes):  
    1.  Run the following command on primary node to start the cluster:
        ```
        cortx cluster start
        ```

    1.  Verify Cortx cluster status:  
        ```
        hctl status
        ```

# Auto Deploy VM (One Click Deployment - Provided Component Mini-Provisioners Comply)  
1.  Define ISO variables
    ```
    SINGLE_ISO=$(ls -1 /opt/isos/cortx-*-single.iso)
    OS_ISO=$(ls -1 /opt/isos/cortx-os-*.iso)
    ```
1.  Run auto_deploy_vm provisioner cli command:
    ## Single Node VM
    **If using remote hosted repos**:  
    ```
    provisioner auto_deploy_vm \
        --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
        --source iso --config-path ~/config.ini \
        --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
        srvnode-1:$(hostname -f)
    ```

    ## Multi Node VM
    **If using remote hosted repos**:  
    ```
    provisioner auto_deploy_vm \
        --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
        --source iso --config-path ~/config.ini \
        --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
        srvnode-1:<fqdn:primary_hostname> \
        srvnode-2:<fqdn:secondary_hostname> \
        srvnode-3:<fqdn:secondary_hostname>
    ```
    Example:
    ```
    provisioner auto_deploy_vm \
        --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
        --source iso --config-path ~/config.ini \
        --iso-cortx ${SINGLE_ISO} --iso-os ${OS_ISO} \
        srvnode-1:host1.localdomain srvnode-2:host2.localdomain srvnode-3:host3.localdomain
    ```
    **NOTE**:  
    1.  This command will ask for each node's **root password** during initial cluster setup.  
    This is one time activity required to setup password-less ssh across nodes.  
    1.  [OPTIONAL] For setting up a cluster of more than 3 nodes do append `--name <setup_profile_name>` to auto_deploy_vm command input parameters.  

1.  Start cluster (irrespective of number of nodes):  
    **NOTE**: Run this command only on primary node (srvnode-1).  
    ```
    cortx cluster start
    ```

1.  Check if the cluster is running:  
    ```
    hctl status
    ```


## Known issues:  
1.  Known Issue 19: [Known Issue 19: LVM issue - auto-deploy fails during provisioning of storage component (EOS-12289)](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-Stack#manual-fix-in-case-the-node-has-been-reimaged)  
