# Auto Deploy - Provisioner CLI Commands for HW

`auto_deploy` CLI command will setup Salt, Provisioner and deploy all components on both nodes.

Salt configuration will have multi-master support to recover/replace a node, if failed. 

# Before You Start: Pre-requisites  

Checklist:
  - [ ]  **Do you have both ISOs (OS and CORTX) _and_ corresponding `cortx-prep-<version>.sh` script?**
  - [ ]  Do you have the right Management VIP for the setup?  
  - [ ]  Do you have the right Cluster IP for the setup?  
  - [ ]  Do you have the IP address for public data network for each server (replace `enp175s0f0` with proper interface name): `ip a | grep inet | grep enp175s0f0 | egrep -v 'secondary|inet6'`? 
  - [ ]  Do you see the LUNs on the execution of this command: `lsblk -S`?  
  - [ ]  Do both the systems on your setup have valid hostnames, are the hostnames accessible: ping <hostname>?  
  - [ ]  Do you have a valid Username/Password for BMC on both server nodes? Have you tested them?  
  - [ ]  Have you setup In-band? 
  - [ ]  Do you have IPs for both storage controllers? (for inband these should be `10.0.0.2` & `10.0.0.3`)?  
  - [ ]  Do you have the username and password for the controllers?  
  - [ ]  Have you checked if the controllers are accessible with the data that you have collected?  
  - [ ]  Did you check connectivity to Controller-A? `ssh <controller_username>@<controller_a_ip>` (use controller password)  
  - [ ]  Did you check connectivity to Controller-B? `ssh <controller_username>@<controller_b_ip>` (use controller password)   
  - [ ]  Have you disabled cross-connect using `lsiutil` (refer to [this document](https://seagatetechnology.sharepoint.com/:w:/r/sites/eos.devops/_layouts/15/Doc.aspx?sourcedoc=%7B0043C622-C96A-41B7-B636-AA0539FEDA2C%7D&file=Deployment%20Within%20Seagate%20Labs.docx&action=default&mobileredirect=true) for the usage instructions)?
  - [ ]  Are you reinstalling the existing setup? If so, have you applied a workaround to clean up the existing LVM metadata on the enclosure volumes ([method 1](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-Stack#manual-fix-in-case-the-node-has-been-reimaged), [method 2](https://github.com/Seagate/cortx-prvsnr/wiki/Alternative-method-for-removing-LVM-metadata-information-from-enclosure-volumes))?
  - [ ]  Do both HW nodes have Mellanox drivers installed? (If having Mellanox cards for high-speed data network)?
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

# Using `provisioner auto_deploy` CLI 

## Method-1: Using local ISOs

This is the **primary deployment method** for CORTX software.

1.  Install the OS on both servers
    1. If using the Satellite-based method, proceed to the next step
    1. If using the USB-based method, update the hostnames (FQDN) on both servers. Run:

    ```
    hostnamectl set-hostname --static --transient --pretty <FQDN>
    ```

1.  Verify In-Band configuration (it should be done automatically, regardless of method of OS installation)

1.  Using `lsiutil`, disable cross-connect

1.  If reinstalling the existing system, apply the workaround for LVM metadata

1.  Ensure `/etc/yum.repos.d` is empty on all participating nodes

1.  Download both ISOs **and** corresponding `cortx-prep-<version>.sh` script to **both** servers to `/opt/isos`. Run:

    ```
    cd /opt/isos
    curl -O https://<RE_server>/software_release/cortx-os-<version>.iso
    curl -O https://<RE_server>/software_release/cortx-<version>-single.iso
    curl -O https://<RE_server>/software_release/cortx-prep-<version>.sh
    ```
    Replace `<version>` with the correct version. 

    **Note.** Please ensure that only one ISO file of each type (single and os) is located there.

1.  Log in to [future] primary server (Server-A) and change permissions of `/opt/isos/cortx-prep-<version>.sh`. Run:

    ```
    chmod +x /opt/isos/cortx-prep-<version>.sh
    ```

1.  From Server-A, execute `cortx-prep-<version>.sh` to install Provisioner and required libraries and python modules. Run:

    ```
    /opt/isos/cortx-prep-<version>.sh
    ```

1.  Create `config.ini` file. Refer to [this section](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands/#configini-example) for an example.

1.  Download `config.ini` to the primary server (Server-A), for example, to `/root`

1.  Install CORTX software using local ISOs. Run:

    ```
    provisioner auto_deploy --console-formatter full --logfile --logfile-filename /var/log/seagate/provisioner/setup.log \
      --source iso --config-path /root/config.ini --ha \
      --iso-cortx /opt/isos/cortx-<version>-single.iso 
      --iso-os /opt/isos/cortx-os-<version>.iso \
      srvnode-1:st1-node-a.colo.seagate.com \
      srvnode-2:st1-node-b.colo.seagate.com
    ```
    Replace `<version>` with the correct version.

    **NOTE:** This command will ask for nodes' passwords during the initial cluster setup.

1.  Verify the installation. Refer to [this section](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands/#cluster-installation-verification) for the list of commands. Refer below for an example of `pcs status` output.

    ```
    [root@smcxx-xx ~]# pcs status
    Cluster name: cortx_cluster
    Stack: corosync
    Current DC: srvnode-2 (version 1.1.21-4.el7-f14e36fd43) - partition with quorum
    Last updated: Tue Nov 17 06:33:58 2020
    Last change: Tue Nov 17 05:38:16 2020 by root via cibadmin on srvnode-1
    2 nodes configured
    71 resources configured
    Online: [ srvnode-1 srvnode-2 ]
    Full list of resources:
     Clone Set: ClusterIP-clone [ClusterIP] (unique)
         ClusterIP:0        (ocf::heartbeat:IPaddr2):       Started srvnode-1
         ClusterIP:1        (ocf::heartbeat:IPaddr2):       Started srvnode-2
     stonith-c1     (stonith:fence_ipmilan):        Started srvnode-2
     stonith-c2     (stonith:fence_ipmilan):        Started srvnode-1
     Clone Set: lnet-clone [lnet]
         Started: [ srvnode-1 srvnode-2 ]
     Resource Group: c1
         ip-c1      (ocf::heartbeat:IPaddr2):       Started srvnode-1
         consul-c1  (systemd:hare-consul-agent-c1): Started srvnode-1
         lnet-c1    (ocf::cortx:lnet):      Started srvnode-1
         var-motr1  (ocf::heartbeat:Filesystem):    Started srvnode-1
         hax-c1     (systemd:hare-hax-c1):  Started srvnode-1
         motr-confd-c1      (systemd:m0d@0x7200000000000001:0x9):   Started srvnode-1
         motr-ios-c1        (systemd:m0d@0x7200000000000001:0xc):   Started srvnode-1
         io_path_health-c1  (ocf::seagate:hw_comp_ra):      Started srvnode-1
     Resource Group: c2
         ip-c2      (ocf::heartbeat:IPaddr2):       Started srvnode-2
         consul-c2  (systemd:hare-consul-agent-c2): Started srvnode-2
         lnet-c2    (ocf::cortx:lnet):      Started srvnode-2
         var-motr2  (ocf::heartbeat:Filesystem):    Started srvnode-2
         hax-c2     (systemd:hare-hax-c2):  Started srvnode-2
         motr-confd-c2      (systemd:m0d@0x7200000000000001:0x52):  Started srvnode-2
         motr-ios-c2        (systemd:m0d@0x7200000000000001:0x55):  Started srvnode-2
         io_path_health-c2  (ocf::seagate:hw_comp_ra):      Started srvnode-2
     Clone Set: motr-kernel-clone [motr-kernel]
         Started: [ srvnode-1 srvnode-2 ]
     motr-free-space-mon    (systemd:motr-free-space-monitor):      Started srvnode-1
     Clone Set: ldap-clone [ldap]
         Started: [ srvnode-1 srvnode-2 ]
     Clone Set: s3auth-clone [s3auth]
         Started: [ srvnode-1 srvnode-2 ]
     Clone Set: els-search-clone [els-search]
         Started: [ srvnode-1 srvnode-2 ]
     Clone Set: statsd-clone [statsd]
         Started: [ srvnode-1 srvnode-2 ]
     haproxy-c1     (systemd:haproxy):      Started srvnode-1
     haproxy-c2     (systemd:haproxy):      Started srvnode-2
     Clone Set: rabbitmq-clone [rabbitmq]
         Started: [ srvnode-1 srvnode-2 ]
     s3backcons-c1  (systemd:s3backgroundconsumer): Started srvnode-1
     s3backcons-c2  (systemd:s3backgroundconsumer): Started srvnode-2
     s3backprod     (systemd:s3backgroundproducer): Started srvnode-2
     s3server-c1-1  (systemd:s3server@0x7200000000000001:0x22):     Started srvnode-1
     s3server-c1-2  (systemd:s3server@0x7200000000000001:0x25):     Started srvnode-1
     s3server-c1-3  (systemd:s3server@0x7200000000000001:0x28):     Started srvnode-1
     s3server-c1-4  (systemd:s3server@0x7200000000000001:0x2b):     Started srvnode-1
     s3server-c1-5  (systemd:s3server@0x7200000000000001:0x2e):     Started srvnode-1
     s3server-c1-6  (systemd:s3server@0x7200000000000001:0x31):     Started srvnode-1
     s3server-c1-7  (systemd:s3server@0x7200000000000001:0x34):     Started srvnode-1
     s3server-c1-8  (systemd:s3server@0x7200000000000001:0x37):     Started srvnode-1
     s3server-c1-9  (systemd:s3server@0x7200000000000001:0x3a):     Started srvnode-1
     s3server-c1-10 (systemd:s3server@0x7200000000000001:0x3d):     Started srvnode-1
     s3server-c1-11 (systemd:s3server@0x7200000000000001:0x40):     Started srvnode-1
     s3server-c2-1  (systemd:s3server@0x7200000000000001:0x6b):     Started srvnode-2
     s3server-c2-2  (systemd:s3server@0x7200000000000001:0x6e):     Started srvnode-2
     s3server-c2-3  (systemd:s3server@0x7200000000000001:0x71):     Started srvnode-2
     s3server-c2-4  (systemd:s3server@0x7200000000000001:0x74):     Started srvnode-2
     s3server-c2-5  (systemd:s3server@0x7200000000000001:0x77):     Started srvnode-2
     s3server-c2-6  (systemd:s3server@0x7200000000000001:0x7a):     Started srvnode-2
     s3server-c2-7  (systemd:s3server@0x7200000000000001:0x7d):     Started srvnode-2
     s3server-c2-8  (systemd:s3server@0x7200000000000001:0x80):     Started srvnode-2
     s3server-c2-9  (systemd:s3server@0x7200000000000001:0x83):     Started srvnode-2
     s3server-c2-10 (systemd:s3server@0x7200000000000001:0x86):     Started srvnode-2
     s3server-c2-11 (systemd:s3server@0x7200000000000001:0x89):     Started srvnode-2
     Master/Slave Set: sspl-master [sspl]
         Masters: [ srvnode-1 ]
         Slaves: [ srvnode-2 ]
     Resource Group: csm-kibana
         kibana-vip (ocf::heartbeat:IPaddr2):       Started srvnode-1
         kibana     (systemd:kibana):       Started srvnode-1
         csm-web    (systemd:csm_web):      Started srvnode-1
         csm-agent  (systemd:csm_agent):    Started srvnode-1
         mgmt_path_health-c1        (ocf::seagate:hw_comp_ra):      Started srvnode-1
     uds    (systemd:uds):  Started srvnode-1
     sspl_primary_hw        (ocf::seagate:hw_comp_ra):      Started srvnode-1
    Daemon Status:
      corosync: active/enabled
      pacemaker: active/enabled
      pcsd: active/enabled

    ```

1.  Using `lsiutil`, re-enable cross-connect


## Method-2: Using remotely-hosted ISOs

**NOTE:** This method is **NOT** a preferred method of installing CORTX software. However, the method is supported.

1.  Install the OS on both servers
    1. If using the Satellite-based method, proceed to the next step
    1. If using the USB-based method, update the hostnames (FQDN) on both servers. Run:

    ```
    hostnamectl set-hostname --static --transient --pretty <FQDN>
    ```

1.  Verify In-Band configuration (it should be done automatically, regardless of method of OS installation)

1.  Using `lsiutil`, disable cross-connect

1.  If reinstalling the existing system, apply the workaround for LVM metadata

1.  Identify the primary node (Server-A) and install Provisioner and required libraries and python modules on it. Run:

    1.  Install git using yum  
        ```  
        yum install git -y    
        ```  
        **NOTE:** If you used USB-based install method for OS, you may need to download the OS ISO and mount it.

    1.  Install Provisioner API
        ```
        yum install -y python3
        python3 -m venv venv_cortx
        source venv_cortx/bin/activate
        ```  

        For latest **main** branch:  
        ```
        pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@main#subdirectory=api/python 
        ```  

        For latest **cortx-1.0** branch:  
        ```
        pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@cortx-1.0#subdirectory=api/python 
        ``` 

1.  Create `config.ini` file. Refer to [this section](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands/#configini-example) for an example.

1.  Download `config.ini` to the primary server (Server-A), for example, to `/root`

1.  Install CORTX software using remotely-hosted ISOs. Run:
    ```
    provisioner auto_deploy --console-formatter full --logfile \
       --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm \
       --config-path ~/config.ini --ha \
       --dist-type bundle \  
       --target-build '<path to base url for hosted repo>' \  
       srvnode-1:<fqdn:primary_hostname> \
       srvnode-2:<fqdn:secondary_hostname>
    ```
    **NOTE:** `--target-build` should be link to base url to hosted repo.

1.  Verify the installation. Refer to [this section](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands/#cluster-installation-verification) for the list of commands. 

1.  Using `lsiutil`, re-enable cross-connect


## Method-3: Deployment based on component groups

**NOTE:** This method is an **advanced** approach that could be used for development purposes only.

1.  Install the OS on both servers
    1. If using the Satellite-based method, proceed to the next step
    1. If using the USB-based method, update the hostnames (FQDN) on both servers. Run:

    ```
    hostnamectl set-hostname --static --transient --pretty <FQDN>
    ```

1.  Verify In-Band configuration (it should be done automatically, regardless of method of OS installation)

1.  Using `lsiutil`, disable cross-connect

1.  If reinstalling the existing system, apply the workaround for LVM metadata

1.  Identify the primary node (Server-A) and install Provisioner and required libraries and python modules on it. Run:

    1.  Install git using yum  
        ```  
        yum install git -y    
        ```  
        **NOTE:** If you used USB-based install method for OS, you may need to download the OS ISO and mount it.

    1.  Install Provisioner API
        ```
        yum install -y python3
        python3 -m venv venv_cortx
        source venv_cortx/bin/activate
        ```  

        For latest **main** branch:  
        ```
        pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@main#subdirectory=api/python 
        ```  

        For latest **cortx-1.0** branch:  
        ```
        pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@cortx-1.0#subdirectory=api/python 
        ``` 
1. Setup provisioned. Run:
   ```
        yum install -y python36-m2crypto salt salt-master salt-minion python36-cortx-prvsnr
   ```

1.  Create `config.ini` file. Refer to [this section](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands/#configini-example) for an example.

1.  Download `config.ini` to the primary server (Server-A), for example, to `/root`

1. Configure setup using `config.ini` (steps TBD)
 
1. Deploy using component groups:

   1. system component group
      ```
      provisioner deploy_dual --states system
      ```

   2. prereq component group
      ```
      provisioner deploy_dual --states prereq
      ```

   3. sync component group
      ```
      provisioner deploy_dual --states sync
      ```

   4. iopath component group
      ```
      provisioner deploy_dual --states iopath
      ```

   5. ha component group
      ```
      provisioner deploy_dual --states ha
      ```

   6. controlpath component group
      ```
      provisioner deploy_dual --states controlpath
      ```

   7. backup component group
      ```
      provisioner deploy_dual --states backup
      ```

1.  Verify the installation. Refer to [this section](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands/_edit#cluster-installation-verification) for the list of commands. 

1.  Using `lsiutil`, re-enable cross-connect


## `config.ini` example
     
**IMPORTANT NOTE: Please check every detail in this file correctly according to your node.**  
**Verify interface names are correct as per your node**  

        ```
        [cluster]
        cluster_ip=172.19.222.12
        mgmt_vip=10.237.65.63

        [storage]
        type=5U84
        controller.primary.ip=10.237.66.68
        controller.secondary.ip=10.237.65.123
        controller.user=manage
        controller.secret='!manage'
        controller.type=

        [srvnode-1]
        hostname=iu12-r22.pun.seagate.com
        network.mgmt.interfaces=eno1,eno2
        network.data.public_ip=172.19.22.12
        network.data.public_interfaces=enp24s0f0, enp24s0f1
        network.data.private_interfaces=enp24s0f2, enp24s0f3
        bmc.user=ADMIN
        bmc.secret='ADMIN1'

        [srvnode-2]
        hostname=iu10-r22.pun.seagate.com
        network.mgmt.interfaces=eno1
        network.data.public_ip=172.19.22.10
        network.data.public_interfaces=enp24s0f0, enp24s0f1
        network.data.private_interfaces=enp24s0f2, enp24s0f3
        bmc.secret='ADMIN1'
        bmc.user=ADMIN
        ```

        **Optional input** : `public_ip`. Remaining data from `config.ini` is mandatory.

**NOTE: Please add second interface for management network for srvnode-1 (e.g. network.mgmt_nw.iface=eno1,eno2), this is important for configuring the service port.**  

## Cluster installation verification

1.  Once auto_deploy command is executed successfully, verify salt master setup on both nodes (setup verification checklist):

     ```
    salt '*' test.ping  
    salt "*" service.stop puppet
    salt "*" service.disable puppet
    salt '*' pillar.get release  
    salt '*' grains.get node_id  
    salt '*' grains.get cluster_id  
    salt '*' grains.get roles  
    ``` 
        
1.  Verify cortx cluster status:  
    ```
    pcs status
    ```

1.  Get build details:
    ```
    provisioner get_release_version
    ```

# Known issues:  

**Please refer to [the list of known issues](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-Stack) for the full up to date information.**

**Specific highlights / most common issues:**

1. Known Issue 19: [Known Issue 19: LVM issue - auto-deploy fails during provisioning of storage component (EOS-12289)](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-Stack#manual-fix-in-case-the-node-has-been-reimaged)


1. Pillar data changes after node reboot

   Reason: GlusterFS service doesn't automatically start after node reboot.

   Solution: Restart Gluster services and re-mount shared volumes:

   ```
   salt "*" service.start glusterd.service
   salt "*" service.start glusterfsd.service
   salt "*" service.start glusterfssharedstorage.service
   salt "*" cmd.run "mount -a"
   salt "*" saltutil.refresh_pillar
   ```

# Node Replacement  

**replace_node** CLI command helps to recover/replace node from a failed state 

## Prerequisites: 
1.  At least one node must be in a healthy state (salt master should be running)

## Steps: Run Replace Node
Refer Wiki: [Node-Replacement](Node-Replacement)
