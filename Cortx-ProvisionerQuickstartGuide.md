# CORTX-Provisioner Quick Start Guide

This guide provides a step-by-step walkthrough for getting you CORTX-Provisioner ready.

- [1.0 Hardware Checklist](#10-Hardware-Checklist)
- [1.1 Prerequisites](#11-Prerequisites)
- [1.2 Known Issues and Limitations](#12-Known-Issues-and-Limitations)
- [1.3 Dual Node Setup on Hardware](#13-Dual-Node-Setup-on-Hardware)
- [1.4 Teardown CORTX](#14-Teardown-CORTX)
- [1.5 Virtual Machines](#15-Virtual-Machines)
- [1.6 Set up the S3client](#16-Set-up-the-S3client)


## 1.0 Hardware Checklist

Ensure that you have the correct hardware cofiguration before moving on to the prerequisites section.

<details>
  <summary>Click to expand!</summary>
  <p>
    
* [x] Ensure that you are on a Centos 7.7.1908 Operating System.                                                                                                                 

  :page_with_curl: **Notes:** 
  - Install the vanilla OS for Centos 7.7.1908 release. 
  - Ensure you have root credentials.                                      
                                
* [x] Network:                                                                                                
  
  - Single node CORTX setup: Not Applicable
  - Dual node CORTX setup: Ensure that uniform network interfaces are available on both the nodes. 
  
    **Example:** If there are eth0 and eth1 interfaces available on node1, they should be available and have the same names and properties on node2 (subnet, mtu, etc.)  

* [x] Hardware Configuration and Storage:                                                                             
  
  - You'll need a minimum of 2GB space under /opt/ directory or partition.
  - A minimum of two LUNs should be available from the storage controller or two raw disks locally available on the system (one for metadata and one for data.) 
  
* [x] Miscellaneous:
  
- Ensure that your hardware is connected to cortx-storage.colo.seagate.com.
- You'll need internet connectivity to download and install third-party open source softwares. 
- You'll have to open the following ports:                                                                                                
  - 80 haproxy
  - 443 haproxy
  - 8100 CSM        
  
* [x] Disable SE Linux.  

  Follow these steps to disable SE Linux:  
  
  1. Run `$ vi /etc/selinux/config`
  2. Configure SELINUX=disabled in the /etc/selinux/config file using `$ vi /etc/selinux/config` 
  3. Set SELINUX=disabled 
    
      ```shell
    
          # This file controls the state of SELinux on the system.
          # SELINUX= can take one of these three values:
          #     enforcing - SELinux security policy is enforced.
          #     permissive - SELinux prints warnings instead of enforcing.
          #     disabled - No SELinux policy is loaded.
          SELINUX=disabled
          # SELINUXTYPE= can take one of three two values:
          #     targeted - Targeted processes are protected,
          #     minimum - Modification of targeted policy. Only selected processes are protected.
          #     mls - Multi Level Security protection.
          SELINUXTYPE=targeted
      ```  
   4. Restart your node using: 
    
      `$ shutdown -r now`
    
   5. After rebooting your system, confirm that the getenforce command returns a `Disabled` status:
    
      `$ getenforce`
    
* [x] Provision your Controller: ensure that the storage controller attached to the servers is correctly configured with pools and volumes. 

  The Base Command to provision your controller is:
  
  	`./controller-cli.sh host -h '<controller host>' -u <username> -p '<password>'`
  
  	Where:
	- -h: hostname or IP address of controller
  	- -u: Username of the controller
  	- -p: Password for the Username 

   **Usage:** The code below shows the syntax for using the base command: 
    	
	 ```shell
	
	 ./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin'
	 ```
	
	 or 
	
	 ```shell
	
	 ./controller-cli.sh host -h '192.168.1.1' -u admin -p '!admin'
	 ```

   **Basic Commands**
   
   1. For help, use:
   
      `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' -h | --help`
	
   2. To view the details of the provisioning setup present on your storage enclosure, use:
   	      
      `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov -s | --show-prov`
   
   **Controller provisioning**
   
     You can provision the cotroller in two ways:
      
    1. Standard Provisioning: to provision the controller on 'host.seagate.com' with a standard configuration of 2 linear pools with 8 volumes per pool, use:
       
       `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov [-a | --all]`

    2. Custom Provisioning:
       
       1. To provision the controller on 'host.seagate.com' with adapt linear pool dg01, disks range in 0.0-41, and default 8 volumes, use:
       
       	  `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov -t linear -l adapt -m dg01 -d 0.0-41`
       2. To provision the controller on 'host.seagate.com' with raid5 virtual *pool a*, disks range in 0.42-83, and default 8 volumes, use:
       
           `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov -t virtual -l r6 -m a -d 0.42-83`
       3. To provision the controller on 'host.seagate.com' with raid5 virtual *pool b*, disks range in 0.0-9, and 6 volumes, use:
            
	    	`./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov -t virtual -l r5 -m b -d 0.0-9 -n 6`
	    
	     	:page_with_curl: **Notes:** 
	        	- -t,-l,-m,-d flags are necessary for custom controller provisioning.
	 		- Supported Custom Parameters:
	   			- Pool-types: linear and virtual
	   			- Levels: r1,r5,r6,r10,r50, and adapt
	   			- Pool-names for virtual pools: a and b 
	   			- Number of volumes: 1,2,3,4,5,6,7, and 8

   4. To eliminate existing standard or custom provisioning on 'host.seagate.com' controller, use:
   
      `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov [-c | --cleanup]`
   
   5. To eliminate existing standard or custom provisioning on 'host.seagate.com' controller, and set up standard provisioning on it, use:
   
      `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' prov [-c | --cleanup] [-a | --all]`
      
       :page_with_curl: **Note:** You can use the cleanup flag with custom provisioning.
    
    6. To view the details about available disks on storage enclosure, use:
    
       `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' [-s|--show-disks]`
    7. Print storage enclosure serial number, firmware version, and license details present on controller 'host.seagate.com'
   
       `./controller-cli.sh host -h 'host.seagate.com' -u admin -p '!admin' --show-license` 
    
    </p>
    </details>

## 1.1 Prerequisites

<details>
 <summary>Before you begin</summary>
 <p>
  
  1. Verify and ensure that the IPMI is configured and BMC IPs are assigned on both nodes.
  2. Ensure that you've installed RHEL 7.7 OS and the kernel version is 3.10.0-1062.el7.x86_64. 
  3. Run command `lsb_release -a` to verify that the LSB Module is installed.
  4. Make sure that direct network connection is established between two server nodes for private data network.     
  5. For Provisioner to deploy successfully on RHEL servers, you'll need to either enable or disable the subscription manager with standard RHEL and RHEL HA licenses. You'll need to run the CORTX prerequisite script based on the enabled or disabled licenses on your systems. If you are on a CentOS RedHat system, you can directly run the prerequisite script. 
     1. You'll need to check whether licenses are enabled on both the servers. To do that, verifying if the subscription manager is enabled by using:

         ```shell
            $ subscription-manager list | grep Status: | awk '{ print $2 }' 
            && subscription-manager status | grep "Overall Status:" | awk '{ print $3 }'
         ```
          
        **Output**
          
          ```shell
          
            Subscribed  
            Current  
          ```     
          
        - If you get the above output message, then subscription manager is enabled on your system. 
        - If you do not get the above output message, subscription manager is disabled. 
          - Run the following prerequisite script to enable the subscription manager: 
          `$ curl https://raw.githubusercontent.com/Seagate/cortx-prvsnr/Cortx-v1.0.0_Beta/cli/src/cortx-prereqs.sh?token=APVYY2OPAHDGRLHXTBK5KIC7B3DYG -o cortx-prereqs.sh; chmod a+x cortx-prereqs.sh; ./cortx-prereqs.sh --disable-sub-mgr`   
      
     2. Verify if High Availability license is enabled on your system by using:   
      
          `$ subscription-manager repos --list | grep rhel-ha-for-rhel-7-server-rpms`
          
          **Output**
          
          `Repo ID:   rhel-ha-for-rhel-7-server-rpms`
     
        - If the High Availability repository is listed in the output message above, then the High Availability license is also enabled. 
        - If you do not see the High Availability repository listed in the output message, then the High Availability license is not enabled on your system. You can do any one of the following:
          1. Get the High Availability license enabled on both nodes by your Infrastructure team.  
          2. Deploy CORTX with subscription manager disabled on both nodes.   

     3. You can deploy CORTX with or without the subscription manager. Before you deploy CORTX, ensure that: 
        1. You've installed mellanox drivers on both nodes. To install mellanox, run the CORTX prerequisite script:
           
           `curl https://raw.githubusercontent.com/Seagate/cortx-prvsnr/main/cli/src/cortx-prereqs.sh?token=APVYY2KMSGG3FJBCA73EUZC7B3BYG | bash -s`   
         - Once the Mellanox Drivers are installed, your system will reboot. 
         - If Mellanox Drivers are installed on your system already, the system will not reboot. 
        2. Seagate internal repositories are set up manually from `/etc/yum.repos.d/`.
     
        Run the CORTX prerequisite script:
         
         1. To deploy CORTX with the subscription manager enabled, use:   
             1. Navigate to [GitHub](https://github.com/Seagate/cortx-prvsnr).
             2. Select the *DEV* or *BETA* branch. For the latest code, select the *release* branch. 
             3. Click cli and navigate to src.
             4. Click cortx-prereqs.sh and view the RAW file. 
             5. Copy the token link for your Prerequisite script.   
             
                `curl https://raw.githubusercontent.com/Seagate/cortx-prvsnr/main/cli/src/cortx-prereqs.sh?token=APVYY2KMSGG3FJBCA73EUZC7B3BYG | bash -s`   

         2. To deploy CORTX with the subscription manager enabled, use:
        
            `curl https://raw.githubusercontent.com/Seagate/cortx-prvsnr/Cortx-v1.0.0_Beta/cli/src/cortx-prereqs.sh?token=APVYY2OPAHDGRLHXTBK5KIC7B3DYG -o cortx-prereqs.sh; chmod a+x cortx-prereqs.sh; ./cortx-prereqs.sh --disable-sub-mgr`   
      
         :page_with_curl: **Notes:** 
         - You'll need to generate your own tokens for Dev, Release and Beta Builds.
         - To deploy the Beta build, replace `main` with `Cortx-v1.0.0_Beta` in the token url.     

 </p>
 </details>

## 1.2 Known Issues and Limitations

   Before running the commands, please go through the list of [Known Issues for dual node setup](https://github.com/Seagate/cortx-prvsnr/wiki/deploy-eos)

   :warning: **Limitation:** 
   
   [Single node hardware setup](https://github.com/Seagate/cortx-prvsnr/wiki/Single-node-setup) is currently not supported by CORTX-Provisioner. 
  

## 1.3 Dual Node Setup on Hardware

   1. Ensure that you meet the [Prerequisites](#11-Prerequisites) and your systems are rebooted.  
   2. Make sure that all the volumes or LUNs mapped from the storage enclosure to the servers, are visible on both the servers. 
   3. Run command: 
   
      `$ lsblk -S|grep SEAGATE`

<details>
 <summary>View Output</summary>
 <p>
    
 ```shell
    
    [root@sm10-r20 ~]# lsblk -S|grep SEAGATE
    sda  0:0:0:1    disk SEAGATE  5565             G265 sas
    sdb  0:0:0:2    disk SEAGATE  5565             G265 sas
    sdc  0:0:0:3    disk SEAGATE  5565             G265 sas
    sdd  0:0:0:4    disk SEAGATE  5565             G265 sas
    sde  0:0:0:5    disk SEAGATE  5565             G265 sas
    sdf  0:0:0:6    disk SEAGATE  5565             G265 sas
    sdg  0:0:0:7    disk SEAGATE  5565             G265 sas
    sdh  0:0:0:8    disk SEAGATE  5565             G265 sas
    sdi  0:0:1:1    disk SEAGATE  5565             G265 sas
    sdj  0:0:1:2    disk SEAGATE  5565             G265 sas
    sdk  0:0:1:3    disk SEAGATE  5565             G265 sas
    sdl  0:0:1:4    disk SEAGATE  5565             G265 sas
    sdm  0:0:1:5    disk SEAGATE  5565             G265 sas
    sdn  0:0:1:6    disk SEAGATE  5565             G265 sas
    sdo  0:0:1:7    disk SEAGATE  5565             G265 sas
    sdp  0:0:1:8    disk SEAGATE  5565             G265 sas
    [root@sm10-r20 ~]# 
  ```
    
</p>
</details>

   :page_with_curl: **Notes:** 
    
   - If you do not see the disk devices listed, as shown in the oputput above, please don't proceed. 
   	- Try rebooting the servers and check again. 
   - If you still do not see the disks listed, contact your infrastructure team. 
   
   4. You'll need to deploy CORTX. There are two ways in which you can do this:  
   		
	  1. [Auto-deploy 2-node CORTX cluster on hardware using a single command](https://github.com/Seagate/cortx-prvsnr/wiki/Deployment-on-HW_Auto-Deploy).   
	  2. [Manually deploy CORTX setup on a VM singlenode](https://github.com/Seagate/cortx-prvsnr/wiki/Cortx-setup-on-VM-singlenode). 
	  

## 1.4 Teardown CORTX  
  
Teardown allows user to remove components and cleanup what had been setup as part of provisioning. This could be achieved either for entire system or for each component individually. Since there are various inter dependencies of Cortx cluster services the same script to teardown cluster does not always work and the Cortx cluster needs different ways of teardown in different situation or scenarios.  

The following sections elucidate steps that you can run in such scenarios:   

<details>
	<summary>Click to expand</summary>
	<p>
		
#### 1. Teardown cluster when the cluster is unstable and destroy itself is hung:    

A cluster can be unhealthy if:
  - One or more than one services or pcs resources are listed with status as Stopped/Offline   
  - Cluster is in failed-over state.  
  - Cluster is partially teared down  
  - Cluster is teared down in wrong sequence  

In such scenarios the destroy may get stuck somewhere due to some unknown reason. If the destroy is stuck at some point for more that 30 minutes, check what service the salt-minion is running. To do so, keep the destroy running on one session and open another ssh session for the same host (primary) and keep checking the running processes:   

1. Run `$ ps -e f`  - This will list the processes in hierarchical manner 

   Here's a snippet of the ps output:   

  	```shell
  
  		206342 ?        Sl     0:00 /usr/bin/python3.6 -s /usr/bin/salt-minion
  		206465 ?        S      0:00  \_ bash /opt/seagate/cortx/hare/libexec/prov-ha-reset None
  		206510 ?        S      0:00      \_ /usr/bin/python2 -Es /usr/sbin/pcs resource delete c2
  		206516 ?        S      0:00          \_ /usr/sbin/crm_resource --wait
  	```

2. Destroy will run salt commands to teardown the components one after another. Like in above output the salt minion has invoked process 206510 to delete resource c2 ( pcs resource delete c2) which further has invoked process 206516 (crm_resource —wait).

3. To check if it’s proceeding or struck at  process 206516 keep running `ps -e f` command every 2-3 minutes, if it’s proceeding it will list the different  process under salt-minion. If it’s still shows the same command for more than 10-15 minutes it can be assumed that the command is stuck for deleting resource C2. In such scenario, to make destroy proceed ahead kill the stuck process (the last pid in the hierarchy)   
  
  	`$ kill -9 206516`  - this will proceed with destroy.  

4. If it doesn’t, check the processes on second node and follow the same steps mentioned above. Repeat the same process if the destroy is stuck tearing down a next component.
5. Once destroy completes successfully, you'll need to reboot the nodes. 

#### 2. Wipe out everything including provisioner packages:
    
🛑 **Caution:** This will wipe out everything including salt and provisioner packages.

1. To wipe out everything at once, run:

   `$ sh /opt/seagate/cortx/provisioner/cli/destroy`    
  
   :page_with_curl: **NOTE:** You may get some failures, ignore them.  
 
2. Remove Provisioner, salt and cleanup /opt/seagate directory:  
  
    `$ sh /opt/seagate/cortx/provisioner/cli/destroy --remove-prvsnr`  
  
3. Check and confirm if required rpms are removed on both nodes:  
      
   `$ rpm -qa | grep -E "cortx|salt"`  
      
   If any rpms are still there, remove them manually from both nodes:  
   
    ```shell 
     
      	  $ for pkg in `rpm -qa | grep -E "cortx|salt"`; do yum remove -y $pkg; done 
      	  $ rm -rf /etc/salt* && rm -rf /opt/seagate && rm -rf /root/.ssh/*   
     ```  

#### 3. Teardown only Cortx components all at once:
:page_with_curl: **Note:** This will remove all the Cortx components, excluding Provisioner. We've listed the components that will be removed:   

*   CSM  
*   SSPL  
*   HA(corosync pacemaker)  
*   Hare  
*   S3server  
*   Motr  
*   Lustre  
*   Rabbitmq  
*   Kibana  
*   Elasticsearch  
*   Statsd  
*   Openldap  
*   To remove configuration for other system components (cleanup storage partitions, etc), run the command: 
	
	`$ sh /opt/seagate/cortx/provisioner/cli/destroy`  

#### 4. Teardown only specific group components  

   `destroy` now supports tearing down specific group states. Provisioner has grouped up following components states:   

   - iopath-states: lustre, motr, s3server, and hare
   - ha-states: corosync-pacemaker and iostack-ha
   - ctrlpath-states: sspl and csm  

1. To teardown only cortx proprietary components i.e. motr, s3server, hare, sspl & csm, execute:

   `$ sh /opt/seagate/cortx/provisioner/cli/destroy --ctrlpath-states --ha-states --iopath-states`  

2. To teardown a specific group state, run: 

  :warning: **Caution:** It is recommended that you run this command only if you understand the interdependecies between group-states.
  
   1. To teardown only ctrlpath states (sspl, csm) run:  
  
       `$ sh /opt/seagate/cortx/provisioner/cli/destroy --ctrlpath-states`  
     
   2. To teardown only ha states (corosync-pacemaker, iostack-ha) run:  
  
     	`$ sh /opt/seagate/cortx/provisioner/cli/destroy --ha-states`   
     
   3. To teardown only iopath states (lustre, motr, s3server, hare) run: 
  
      	`$ sh /opt/seagate/cortx/provisioner/cli/destroy --iopath-states`  
      
       :page_with_curl: **NOTE:** iopath states has dependency with ha-states, so use it cautiously, like following: 
     
      `$ sh /opt/seagate/cortx/provisioner/cli/destroy --iopath-states --ha-states`  
  
  
#### 5. Reinstall CORTX proprietary components with a different build   

   - The Following steps will re-install proprietary CORTX components like motr, s3server, hare, sspl & csm and;  
   - Keep the provisioner & third party components like haproxy, openldap, etc. as is.  
  
     :page_with_curl: **Notes:** 
  
      - Due to interdependency of the Cortx components, it's advised to do it only if you have the knowledge of component dependencies.  
      - If the new build has provisioner changes that are required for some component then this is not recommended.  

  1. To teardown only Cortx proprietary components i.e. motr, s3server, hare, sspl & csm, execute:
  
     `$ sh /opt/seagate/cortx/provisioner/cli/destroy --ctrlpath-states --ha-states --iopath-states`  
     
      1. To cleanup the failed services, run
       
       	  `$ systemctl reset-failed`  
  
      2. To update new target_build in release.sls. if you want to install cortx compononts from some other build.  

    	 ```shell
    
    	      $ cat /opt/seagate/cortx/provisioner/pillar/components/release.sls | grep target_build
              target_build: http://cortx-storage.colo.seagate.com/releases/cortx/github/release/prod/  
         ```  

  2. Ensure all prerequisites services are up and running:  
  
    	`$ for service in firewalld slapd haproxy kibana elasticsearch statsd rabbitmq-server; do echo "$service"; salt '*' service.start $service; done`  
    
     :page_with_curl: **Note:** If any service is not started (reported False in above command), troubleshoot why it is failing to start. Fix it and then move to the next step.  
  
  3. Re-deploy CORTX proprietary components with the target build updated in release.sls file in previous step:
  
    	`$ /opt/seagate/cortx/provisioner/cli/deploy --iopath-states --ha-states --ctrlpath-states`    

  4. Check if the cluster has started: 
    
    	`$ pcs cluster status`  

  5. Check if all the services in cluster are running: 
    
    	`$ pcs status` - the pcs status should show all the services started and cluster online.

  6. Check if all required services are up and running:  
  
     `$ for service in firewalld slapd haproxy s3authserver lnet kibana elasticsearch statsd rabbitmq-server csm_web csm_agent sspl-ll pcsd ; do echo "$service"; salt '*' service.status $service; done`  

#### 6. For Advanced users - to teardown the installed CORTX components individually using salt commands: 

   :page_with_curl: **Note:** Removing individual components one by one will break the Cortx cluster run only if you know what you are doing.
   
   Execute the following command(s) to tear down the cortx components one by one:

  1. Remove Management stack  
  
     ```
     
       $ salt '*' state.apply components.csm.teardown
       $ salt '*' state.apply components.sspl.teardown
     ```

  2. Remove Data stack  
     
     ```
       $ salt '*' state.apply components.ha.iostack-ha.teardown
       $ salt '*' state.apply components.hare.teardown
       $ salt '*' state.apply components.s3server.teardown
       $ salt '*' state.apply components.motr.teardown
     ```
     
  3. Remove pre-reqs  
  
     ```
       $ salt '*' state.apply components.ha.haproxy.teardown
       $ salt '*' state.apply components.ha.corosync-pacemaker.teardown
       $ salt '*' state.apply components.misc_pkgs.openldap.teardown
       $ salt '*' state.apply components.misc_pkgs.statsd.teardown
       $ salt '*' state.apply components.misc_pkgs.rabbitmq.teardown
       $ salt '*' state.apply components.misc_pkgs.nodejs.teardown
       $ salt '*' state.apply components.misc_pkgs.kibana.teardown
       $ salt '*' state.apply components.misc_pkgs.elasticsearch.teardown
       $ salt '*' state.apply components.misc_pkgs.ssl_certs.teardown
     ```
     
     </p>
     </details>
  
## 1.5 Virtual Machines
  
   To set up up CORTX on a Single Node VM, follow these steps:
   
   <details>
	<summary>Click to expand!</summary>
	<p>
		
   1. Install Provisioner CLI rpm (cortx-prvsnr-cli) from from the CORTX release repo:   
       
       `$ yum install -y http://cortx-storage.colo.seagate.com/releases/cortx/integration/centos-7.7.1908/last_successful/$(curl -s http://cortx-storage.colo.seagate.com/releases/cortx/integration/centos-7.7.1908/last_successful/|grep eos-prvsnr-cli-1.0.0| sed 's/<\/*[^>]*>//g'|cut -d' ' -f1)`  
       
   2. Modify contents of file on primary node as suggested below:
   
      `/root/.ssh/config` 

    	```
           Host srvnode-1 <node-1 hostname> <node-1 fqdn>
           HostName <node-1 hostname or mgmt IP>
           User root
           UserKnownHostsFile /dev/null
           StrictHostKeyChecking no
           IdentityFile /root/.ssh/id_rsa_prvsnr
           IdentitiesOnly yes
        ```
    
   3. Execute setup-provisioner script: 
   
      `$ sh /opt/seagate/cortx/provisioner/cli/setup-provisioner -S`  

      :page_with_curl: **Note:** Check `--help` option in setup-provisioner for detailed usage information.
      
   4. Confirm whether the setup-provisioner has established the master-minion communication successfully:     
      
       ```
         $ salt srvnode-1 test.ping  
         srvnode-1:  
         True  
       ```
      
      It should return True for srvnode-1 as shown above. 
      
   5. Install multipath and configure if you are provisioning Hardware:
    
      `$ salt "srvnode-1" state.apply components.system.storage.multipath`  

      **Checklist**  
    
      * [x]  Ensure that you've created volumes on storage and these volumes are available for multipath config.
      * [x]  Verify that the SAS cabling is functional.
  
  6. Prepare the CORTX deployment configuration file: cluster.sls
    
      ```
    	  WIP:  
          1. Auto-update hostname in /opt/seagate/cortx/provisioner/pillar/components/cluster.sls 
          2. Auto-update section ['cluster']['storage_enclosure'] once inband is setup between server and storage.
          3. Freeze section ['cluster']['srvnode-1']['network'] to use mgmt0 and data0 established using kickstart
       ```
      **Example:** hostname of server node, network interface for management, and data channels, storage enclosure details, etc.  
    
       1. Check network interfaces:
          
	  1. To get interfaces:
	 
             `$ ip a`  
	     
	  2. To get route or gateway info:
	  
	     `$ ip r`  
	     
	    	**Output:** 
		
		 ```shell
		 
		   [root@eos-democ-197 /]# ip r
                   default via 10.230.160.1 dev eth0 proto dhcp metric 100 
                   10.230.160.0/21 dev eth0 proto kernel scope link src 10.230.161.141 metric 100 
                   192.168.0.0/24 dev eth1 proto kernel scope link src 192.168.0.194 metric 101
		   ```
	    :page_with_curl: **Notes:**
	    - Identify the network interfaces to be used for mgmt and data channels.
	    - If *data0* and *mgmt0* interfaces are not available on the system, any other interface name can also be provided.
	    	- **Example:** *eth0* for *mgmt0* and *eth1* for *data0*.  
	  
	  3. Update network interfaces, netmask and gateway under section  
	
  
         ```shell
	 
          network:
            mgmt_nw:                  # Management network interfaces
              iface:
                - eno1
                - eno2
              ipaddr: 
              netmask: 
            data_nw:                  # Data network interfaces
              iface: 
                - enp175s0f0
                - enp175s0f0
              ipaddr: 172.19.10.101
              netmask: 255.255.255.0
            gateway_ip: 10.230.160.1              # Gateway IP of network
          ```  
   
   	   4. If you find bond0 already configured, just update the interfaces as below:
	    
          ```
          network:
            mgmt_nw:                  # Management network interfaces
              iface:
                - eno1
              ipaddr: 
              netmask: 
            data_nw:                  # Data network interfaces
              iface: 
                - bond0
              ipaddr:
              netmask: 255.255.255.0
            gateway_ip: 10.230.160.1              # Gateway IP of network
          ```  

    	5. Update *cluster.sls* to provide above details:
	
			`$ vi /opt/seagate/cortx/provisioner/pillar/components/cluster.sls`
	    
	    	:page_with_curl: **Note:** The reference template for single node can be seen at: 											
		
			`/opt/seagate/cortx/provisioner/pillar/components/samples/singlenode.cluster.sls`

			A sample *cluster.sls* for single node CORTX deployment might look like this: 
			
			```shell
     
        		cluster:
          		type: single                           # single/ees/ecs
          		node_list: - srvnode-1
          		srvnode-1:
            		hostname: srvnode-1
            		is_primary: true
            		network:
              		mgmt_nw:                  # Management network interfaces
                		iface:	- eth0
                		ipaddr: 
                		netmask: 255.255.255.0
              		data_nw:                  # Data network interfaces
                		iface: - eth1
                		ipaddr: 
                		netmask: 255.255.255.0
              		floating_ip:
              		gateway_ip:               # Gateway IP of network
            		storage:
              		metadata_device:                # Device for /var/mero and possibly SWAP - /dev/sdb
              		data_devices:                   # Data device/LUN from storage enclosure - /dev/sdc
          		storage_enclosure:
            		id: storage_node_1            # equivalent to fqdn for server node
            		type: RBOD                    # Type of enclosure. E.g. RBOD
              		primary_mc:
                		ip: 127.0.0.1
                		port: 80
              		secondary_mc:
                		ip: 127.0.0.1
                		port: 80
              		user: user
              		password: 'passwd'
 		    ```
	
 			:page_with_curl: **NoteS**: 
			- Values above should be based on target primary or secondary node and leave any other values intact.
			- Failing to provide these details correctly  may result in cluster deployment failure.  

7.  Provide target build for cortx components:

    1. By defualt the target build is last_successful, it is mentioned in the release.sls file as shown below:  
    
    	```shell
    
    		$ cat /opt/seagate/cortx/provisioner/pillar/components/release.sls  
    		cortx_release:
          		target_build: integration/centos-7.7.1908/last_successful  
    	 ```  
    
    2. If you want to change the target build, update this file to provide the build of your choice against *target_build* field in this file  
    
    	```
    	WIP:
      	Release parameter would be accepted as CLI argument for setup-provisioner script as:
      	sh /opt/seagate/cortx/provisioner/cli/setup-provisioner -S --release <build_number>
    	```
	
8.  Setup network bonding:

    :page_with_curl: **Notes**: Currently we lack the confidence for management interface bonding and do not recommend that although the step has been mentioned below:  
    
       1. Setup network and bond data network
	
	   		`$ salt "*" state.apply components.system.network`
		
       2.  Setup network and bond management network. It's crucial to provide correct gateway value in *cluster.sls* for management network to come-up post bonding.
      		
			`$ salt "*" state.apply components.system.network.management`
		
       3. Deploy the single node cluster using `deploy` command:
       
			`$ sh /opt/seagate/cortx/provisioner/cli/deploy -S`  
   
   </p>
   </details>	
  
## 1.6 Set up the S3client   

<details>
	<summary>Prerequisites</summary>
	<p>

Before proceeding with Server setup ensure you have:  
- [Vagrant Setup](https://github.com/Seagate/cortx-prvsnr/wiki/Vagrant-Setup)
- [SaltStack Setup](https://github.com/Seagate/cortx-prvsnr/wiki/SaltStack-Setup)

</p>
</details>

### 1. Prepare Config Files

<details>
	<summary>Click to expand!</summary>
	<p>

1. S3Client provisioning refers to the required data in _pillar/components/s3client.sls_.

	```shell

		s3client:
  		  s3server:
    		    fqdn: srvnode-1
    		    ip: 127.0.0.1        # Optional if FQDN is under DNS
  		access_key: 2lB1wnQKSw2gehG68SzHwA
  		secret_key: Z/xFyapiUnfUBGAXsK+DdJbrQEEyyTie5+uOylO0
  		region: US
  		output: text      # json/text/table
  		s3endpoint: s3.seagate.com
	```  
		
	**Or**

- Run script to set the s3client config:

	```python
	
	$ cd /opt/seagate/cortx/provisioner  
	$ python3 ./utils/configure-eos.py --show-s3client-file-format
	$ python3 ./utils/configure-eos.py --s3client-file <yaml_file_generated_based_on_output_above>
	```
2. Set target release version to be installed:

	`$ cat <prvsnr source>/pillar/components/release.sls`
	
	**Output**
	
	```
	
	   release:
	       target_build: last_successful
	```
	     
**OR**  

- Run script to set the release tag:  

	`$ python <prvsnr source>/utils/configure-eos.py --release ees1.0.0-PI.1-sprint2`  
	
</p>
</details>

### 2. Setup S3Client

<details>
	<summary>Click to expand!</summary>
	<p>
		
   1. Execute Salt formula to setup: `$ salt-call state.apply components.s3clients`  

      - This implicitly installs:  
      	- S3IAMCLI
	- S3Cmd
	- AWSCLI
   2. To uninstall salt formula setup: `$ salt-call --local state.apply components.s3clients.teardown`

#### Independent Setup

###### 1. S3Cmd

1. To setup S3Cmd: 

	`$ salt-call --local state.apply components.s3client.s3cmd`
	
2. To teardown:  

	`$ salt-call --local state.apply components.s3client.s3cmd.teardown`

###### 2. AWSCli

1. To setup AWSCli: 

	`$ salt-call --local state.apply components.s3client.awscli`
	
2. To teardown:  

	`$ salt-call --local state.apply components.s3client.awscli.teardown`
	
</p>
</details>

### 3. Setup COSBench

<details>
	<summary>Click to expand</summary>
	<p>
		
1. To setup COSBench: `$ salt-call --local state.apply components.performance_testing.cosbench`
2. To teardown: `$ salt-call --local state.apply components.performance_testing.cosbench.teardown`

</p>
</details>

## You're All Set & You're Awesome!

We thank you for stopping by to check out the CORTX Community. We are fully dedicated to our mission to build open source technologies that help the world save unlimited data and solve challenging data problems. Join our mission to help reinvent a data-driven world. 

### Contribute to CORTX Provisioner

Please contribute to the [CORTX Open Source project](CONTRIBUTING.md) and join our movement to make data storage better, efficient, and more accessible.

### Reach Out to Us

Please refer to the [Support](SUPPORT.md) section to reachout to us with your questions, suggestions, and feedback.
