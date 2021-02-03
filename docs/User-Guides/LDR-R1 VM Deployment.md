# Auto Deploy VM - Provisioner CLI Commands for Single and Dual node VM

`auto_deploy_vm` CLI command will setup Salt, Provisioner and deploy all components.

Salt configuration will have multi-master support to recover/replace a node, if failed. 


# Before You Start  
Checklist:  
-  [x]  Do you see the devices on execution of this command: lsblk ?  
-  [x]  Do both the systems on your setup have valid hostnames, are the hostnames accessible: ping <hostname>?  
-  [x]  Do you have IPs' assigned to all NICs eth0, eth1 and eth2?  
-  [x]  Identify primary node and run below commands on primary node  
    **NOTE**: For single-node VM, the VM node itself is treated as primary node.  

# VM Preparation for Deployment
1.  Set root user password on both nodes:
    ```  
    sudo passwd root
    ```
1.  Install provisioner api  
    ## Production Environment
    1.  Set repository URL  
        ```
        CORTX_RELEASE_REPO="<URL to Cortx R1 stack release repo>"
        ```
    1.  Install Provisioner API and requisite packages  
        ```
        yum install -y yum-utils
        yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/3rd_party/"
        yum install --nogpgcheck -y python3 python36-m2crypto salt salt-master salt-minion
        rm -rf /etc/yum.repos.d/*3rd_party*.repo
        yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/cortx_iso/"
        yum install --nogpgcheck -y python36-cortx-prvsnr
        rm -rf /etc/yum.repos.d/*cortx_iso*.repo
        yum clean all
        rm -rf /var/cache/yum/
        ```  

    ## Developer Environment
    ```
    yum install git -y
    yum install -y python3
    python3 -m venv venv_cortx
    source venv_cortx/bin/activate
    ```  

    For latest **main** branch:  
    ```
    pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@main#subdirectory=api/python
    ```  
    Append `/usr/local/bin/` to path:  
    `export PATH=$PATH:/usr/local/bin/`  

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
    [storage_enclosure]
    type=other

    [srvnode-1]
    hostname=host1.localdomain
    network.data_nw.pvt_ip_addr=None
    network.data_nw.iface=eth1, eth2
    network.mgmt_nw.iface=eth0
    bmc.user=None
    bmc.secret=None
    ```

    ## Sample config.ini for dual node VM
    ```
    [storage]
    type=other

    [srvnode-1]
    hostname=host1.localdomain
    network.data_nw.pvt_ip_addr=None
    network.data_nw.iface=eth1, eth2
    network.mgmt_nw.iface=eth0
    bmc.user=None
    bmc.secret=None

    [srvnode-2]
    hostname=host2.localdomain
    network.data_nw.pvt_ip_addr=None
    network.data_nw.iface=eth1, eth2
    network.mgmt_nw.iface=eth0
    bmc.user=None
    bmc.secret=None

    ```
    **NOTE** : `private_ip, bmc_secret, bmc_user ` should be None for VM.


# Auto Deploy VM (One Click Deployment - Provided Component Mini-Provisioners Comply)  
1.  Run auto_deploy_vm provisioner cli command:
    
## Single Node VM
**If using remote hosted repos**:  
```
provisioner auto_deploy_vm srvnode-1:$(hostname -f) \
--logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini \
--dist-type bundle --target-build ${CORTX_RELEASE_REPO}
```

## Multi Node VM
**If using remote hosted repos**:  
```
provisioner auto_deploy_vm --console-formatter full --logfile \
    --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm \
    --config-path ~/config.ini --ha \
    --dist-type bundle \
    --target-build '<path to base url for hosted repo>' \
    srvnode-1:<fqdn:primary_hostname> \
    srvnode-2:<fqdn:secondary_hostname> \
    srvnode-3:<fqdn:secondary_hostname>
```
Example:
```
provisioner auto_deploy_vm \
--logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini \
--ha --dist-type bundle --target-build ${CORTX_RELEASE_REPO} \
srvnode-1:host1.localdomain srvnode-2:host2.localdomain srvnode-3:host3.localdomain
```

**NOTE** : 
1. target-build should be link to base url for hosted 3rd_party and cortx_iso repos  

2. For `--target_build` use builds from below url based on OS:  
**centos-7.8.2003**: _<build_url>/centos-7.8.2003/_
OR
Contact Cortx RE team for latest URL.  

3. This command will ask for each node's **root password** during initial cluster setup.  
This is one time activity required to setup password-less ssh across nodes.  

4. For setting up a cluster of more than 3 nodes do append `--name <setup_profile_name>` to auto_deploy_vm command input parameters.  


# Deploy VM Manually:

Manual deployment of VM consists of following steps from Auto-Deploy, which could be individually executed:  
**NOTE**: Ensure [VM Preparation for Deployment](#vm-preparation-for-deployment) has been addressed successfully before proceeding  

**Bootstrap VM(s)**: Run setup_provisioner provisioner cli command:
    
## Single Node VM: Bootstrap
**If using remote hosted repos**:  
```
provisioner setup_provisioner srvnode-1:$(hostname -f) \
--logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini \
--dist-type bundle --target-build ${CORTX_RELEASE_REPO}
```

## Multi Node VM: Bootstrap
**If using remote hosted repos**:  
```
provisioner setup_provisioner --console-formatter full --logfile \
    --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm \
    --config-path ~/config.ini --ha \
    --dist-type bundle \
    --target-build ${CORTX_RELEASE_REPO} \
    srvnode-1:<fqdn:primary_hostname> \
    srvnode-2:<fqdn:secondary_hostname> \
    srvnode-3:<fqdn:secondary_hostname>
```
Example:
```
provisioner setup_provisioner \
--logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini \
--ha --dist-type bundle --target-build ${CORTX_RELEASE_REPO} \
srvnode-1:host1.localdomain srvnode-2:host2.localdomain srvnode-3:host3.localdomain
```

**NOTE** : 
1. target-build should be link to base url for hosted 3rd_party and cortx_iso repos  

1. For `--target_build` use builds from below url based on OS:  
**centos-7.8.2003**: _<build_url>/centos-7.8.2003/_
OR
Contact Cortx RE team for latest URL.  

1. This command will ask for each node's **root password** during initial cluster setup.  
This is one time activity required to setup passwordless ssh across nodes.  

1. For setting up a cluster of more than 3 nodes do append `--name <setup_profile_name>` to auto_deploy_vm command input parameters. 


## Bootstrap Validation
Once deployment is bootstrapped (auto_deploy or setup_provisioner) command is executed successfully, verify salt master setup on both nodes (setup verification checklist)
```
salt '*' test.ping  
salt "*" service.stop puppet
salt "*" service.disable puppet
salt '*' pillar.get release  
salt '*' grains.get node_id  
salt '*' grains.get cluster_id  
salt '*' grains.get roles  
``` 


## Deployment Based On Component Groups:

If provisioner setup is completed and you want to deploy in stages based on component group

### Non-Cortx Group: System & 3rd-Party Softwares
1.  System component group  
    **Single Node**
    ```
    provisioner deploy_vm --states system --setup-type single
    ```
    **Multi Node**
    ```
    provisioner deploy_vm --states system
    ```
1.  Prereq component group  
    **Single Node**
    ```
    provisioner deploy_vm --states prereq --setup-type single
    ```
    **Multi Node**
    ```
    provisioner deploy_vm --states prereq
    ```

### Cortx Group: IO Path & Control Path
1.  IO path component group  
    **Single Node**  
    ```
    provisioner deploy_vm --states iopath --setup-type single
    ```
    **Multi Node**  
    ```
    provisioner deploy_vm --states iopath
    ```
    **Validate**  
    Verify Cortx cluster status:  
    ```
    hctl status
    ```

1.  Control path component group  
    **Single Node**  
    ```
    provisioner deploy_vm --states controlpath --setup-type single
    ```
    **Multi Node**  
    ```
    provisioner deploy_vm --states controlpath
    ```


# VM Teardown
## Teardown Provisioner Deployed Environment
Execute script  
```
/opt/seagate/cortx/provisioner/cli/destroy --ctrlpath-states --iopath-states --prereq-states --system-states
```

## Teardown Provisioner Bootstrapped Environment
To teardown the bootstrap step:  
1.  Unmount gluster volumes  
    ```
    umount $(mount -l | grep gluster | cut -d ' ' -f3)
    ```  
1.  Cleanup bricks and other directories  
    ```  
    # Bricks cleanup
    rm -rf /var/lib/seaagte/cortx
    # Cortx software dirs
    rm -rf /opt/seagate/cortx
    # Cleanup Provisioner profile directory
    rm -rf /root/.provisioner
    # Cleanup Salt
    timeout 5 salt-call saltutil.sync_all
    rm -rf /var/cache/salt
    rm -rf /etc/salt
    ```  
1.  Stop services  
    ```  
    systemctl stop glustersharedstorage glusterfsd glusterd  
    systemctl stop salt-minion salt-master  
    ```  
1.  Uninstall the rpms  
    ```  
    yum erase -y cortx-prvsnr cortx-prvsnr-cli      # Cortx Provisioner packages
    yum erase -y gluster-fuse gluster-server        # Gluster FS packages
    yum erase -y salt-minion salt-master salt       # Salt packages
    yum erase -y python36-cortx-prvsnr              # Cortx Provisioner API packages
    yum autoremove -y
    yum clean all
    rm -rf /var/cache/yum
    ```  
1.  Cleanup SSH  
    ```  
    rm -rf /root/.ssh
    ```  

## Known issues:  
1.  Known Issue 19: [Known Issue 19: LVM issue - auto-deploy fails during provisioning of storage component (EOS-12289)](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-Stack#manual-fix-in-case-the-node-has-been-reimaged)  
