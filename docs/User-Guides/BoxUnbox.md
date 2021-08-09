# Boxing-Unboxing-SW_Update-Factory Install  

- [Boxing](Boxing)
  * [Pre-requisites](Pre-requisites)
  * [Boxing Procedure](Boxing_Procedure)
- [Unboxing](Unboxing)
  * [Pre-requisites](Pre-requisites)
  * [Unboxing Procedure](Unboxing_Procedure)
    - [DHCP Selected](DHCP_Selected)
    - [Static Selected](Static_Selected)
      * [Management Network](Management_Network)
      * [Public Data Network](Public_Data_Network)
      * [BMC Network](BMC_Network)
    

## Boxing  

### Pre-requisites 

1.  Factory setup complete and successful 
1.  Sanity tests executed and successful 

1.  System in healthy state (No failover has happened, and services are functioning as desired) 

### Boxing Procedure  
1.  Ensure all prerequisites are met.  
1.  Execute boxing script as root user:  
    `# sh /opt/seagate/cortx/provisioner/cli/factory_ops/boxing/init --serial SERIAL_NUMBER`
    
    This will:  
    1. Put the cluster in maintenance mode   
    2. Stop all Cortx services   
    3. Create a one time user- 'cortxub'  
    4. Gather and print all necessary information on screen as well as in a text file.  
    5. Shuts down both the servers and resets the controllers.    

1.  At the end of boxing command the following details are posted on screen, it is required for unit shipping and during the unboxing:  

    ```
    **************************************************
    *             Lyve Drive Rack                    *
    **************************************************
    *         Lyve Drive Rack System ID              *
    *------------------------------------------------*
    *                                                *
    *                                                *
    *                                                *
    **************************************************


    **************************************************
    *    CORTX credentials for initial setup         *
    -------------------------------------------------*
      user     : cortxub
      password : dd54cc20d019

      NOTE: Password expires on first login.    

    **************************************************


    **************************************************
    *                 Server A                       *
    *------------------------------------------------*
      Serial Number            :  S264223X9C04397           
      Management Interface MAC : ac:1f:6b:c8:91:ca
      BMC Interface MAC        : ac:1f:6b:cd:a0:2c
      Data Interface MAC       : 98:03:9b:6b:6c:80

    **************************************************


    **************************************************
    *                 Server B                       *
    *------------------------------------------------*
      Serial Number            :  S264223X9C04393
      Management Interface MAC : ac:1f:6b:c8:91:d6
      BMC Interface MAC        : ac:1f:6b:cd:a0:57
      Data Interface MAC       : 98:03:9b:6b:6c:78

    **************************************************
    Note: The above system details are required for unboxing and is stored at: /root/Lyve_rack_SystemID_2020-06-15.txt
      Please replace SystemID with actual System ID in the file name before shipping."
    The cluster nodes are going to shutdown now, please copy the above details  
    Have you copied the above details?  
    ```
    
    **Note:**  
    1. Please copy the file mentioned in the output above (/root/Lyve_rack_SystemID_2020-06-15.txt) to your laptop or some other place other than the server nodes and press y.  
    2. The details printed above and in the file as same, it will be required for printing and pasting it on actual shipping units.  
    3. These details will be required during unboxing command.

1.  This is end of the boxing. Please power-off the storage controllers (Currently they just are reset due to lab access restrictions)  
 
## Unboxing  

### Pre-requisites 

1.  Ensure procedure in Cortx Lyve Drive Rack Edge: PreBoarding requirements  has been followed and networking is configured 
2.  Check if IP addresses for public data interface (enpXXXs0f0) are assigned by DHCP. Run following command (on both nodes):
    
    ```
    [root@sm10-r20 ~]# ip -o addr | grep enp | grep f0
    3: enp175s0f0    inet6 fe80::1e34:daff:fe52:21b8/64 scope link \       valid_lft forever preferred_lft forever
    [root@sm10-r20 ~]# 
    ```

    **Note:** In above example the IP address is not assigned.    

1.  Keep following checklist handy before running unboxing command:  

    * [x] Management network VIP  
    * [x] Data network VIP   
    
    IP addresses for public data interface are **NOT assigned by DHCP**
    * [x] IP address of public data network interface for server A  
    * [x] IP address of public data network interface for server B

   
### Unboxing Procedure 

1.  Use the temporary user generated during boxing to log into node-1 (primary node)  
1.  Update user password  
1.  Sudo as root user  
    `$ sudo su`  
1.  Execute unboxing script as root user: 

    If public data network interfaces are already assigned the static ip addresses (check prerequisite step)   
        `# sh /opt/seagate/cortx/provisioner/cli/factory_ops/unboxing/init -C <Cluster IP> -M <Management Network VIP>`  
1. Make a choice for the type of network settings suitable for the target environment:

    ```
    1. DHCP
    2. Static
    3. Quit
    Choose a network configuration for management network: 
    ```
    
    **Note**: The type of network settings would also be applied to Public Data Network and BMC network

    #### DHCP Selected
    If you select DHCP, the setup would continue to setup the Management (Lower Bandwidth), Public Data (Higher Bandwidth for data IO) and BMC networks to connect to DHCP server for configurations.  
    During the process the script would pause for user inputs to proceed.  

    #### Static Selected
    On selecting Static, the following information would be requested from the user:
    
    1.  **Management Network**

        ```
        Management IP for ${mgmt_if_1} on Server-A:
        Management IP for ${mgmt_if_2} on Server-B:
        Gateway IP for Management interfaces on both nodes:
        DNS search domain for both nodes:
        DNS server IP for both nodes:
        Netmask for Management interfaces on both nodes [255.255.252.0]:
        ```  
        These are self explanatory.  
        
        **Note**: Even though default Netmask value would be set if the user fails to provide one, it is advised to provide a value that conforms to the environment network.  

        Before applying these values, user would be presented with the inputs for verification with a confirmation prompt.  

    1.  **Public Data Network**
    
        ```
        Public Data IP for ${data_if_1} on Server-A:
        Public Data IP for ${data_if_2} on Server-B:
        Gateway IP for Public Data interfaces on both nodes [Optional]:
        Netmask for Public Data interfaces on both nodes [255.255.252.0]:
        ```
        
        **Note**: Gateway is optional if the network is internal on a closed subnet.  
        The Netmask has same advisory as Management network.  

        Before applying these values, user would be presented with the inputs for verification with a confirmation prompt.  

    1.  **BMC Network**
    
        ```
        BMC IP for Server-A:
        BMC IP for Server-B:
        Gateway IP for BMC interfaces on both nodes:
        Netmask for BMC network on both servers [255.255.252.0]:
        ```
        
        **Note**: The advisory is same as management network, although the BMCs could be managed over an entirely different network in some environments.  

        Before applying these values, user would be presented with the inputs for verification with a confirmation prompt.  

    Post setting up of the Networks as mentioned above the unboxing shall proceed with the rest of the Software configuration related activities.  
1.  At the end of unboxing the command waits for the confirmation from user.  
    ```
    **********************************************************   
    Please validate the following:   
      1. Check if all IP addresses have been assigned [run: ip a]   
      2. Check if system has been assigned a hostname [run: hostname -f]   
      3. Check HA cluster is up [run: pcs status].   
      All resources should show as started. Check for fails.]  
    **********************************************************"    
    Does Unboxing look good (y/n)?  
    ```
    Before confirming y or n check if the unboxing is successful by running following commands:   
    
    **Note:** Run and check on both servers.
    $ `ip -o addr`  
      Check if all the IPs are assigned as expected.  
    $ `hostname -f`  
      Check if hostnames are as expected.  
    $ `pcs status`  
      Check if all services are listed as Started.  
      
1.  Put y if everything looks good, this will end the unboxing command with following message:  

    ```
    *************************SUCCESS!!********************************
    The system is ready for use.
    User cortxub has been locked and can no longer be used for login.
    ******************************************************************
    ```  

1.  In case any services are shown as stopped as part of `pcs status` output.        
    e.g.  Cluster_IP resource might be in `stopped` state after unboxing, try to refresh the resource.
    
```
    Clone Set: ClusterIP-clone [ClusterIP] (unique)
     ClusterIP:0        (ocf::heartbeat:IPaddr2):       Stopped
     ClusterIP:1        (ocf::heartbeat:IPaddr2):       Stopped

```

If above output is seen then refresh ClusterIP resource using following command from server A.  

 ``` 
    $ sudo pcs resource refresh ClusterIP:0
      Cleaned up ClusterIP:0 on srvnode-2
      Cleaned up ClusterIP:0 on srvnode-1
      Cleaned up ClusterIP:1 on srvnode-2 
      Cleaned up ClusterIP:1 on srvnode-1
      Waiting for 4 replies from the CRMd.... OK
    $ sudo pcs resource refresh ClusterIP:1
      Cleaned up ClusterIP:0 on srvnode-2
      Cleaned up ClusterIP:0 on srvnode-1 
      Cleaned up ClusterIP:1 on srvnode-2
      Cleaned up ClusterIP:1 on srvnode-1
      Waiting for 4 replies from the CRMd.... OK
   ```
   
   Check if the ClusterIP resources are started now:  
   
   ```
    $ sudo pcs status | grep ClusterIP  
      Clone Set: ClusterIP-clone [ClusterIP] (unique)
         ClusterIP:0        (ocf::heartbeat:IPaddr2):       Started  
         ClusterIP:1        (ocf::heartbeat:IPaddr2):       Started  
   ```
   
1.  If any resources are listed under `Failed resource Actions` as part of pcs status output:   
    **Note:** It's normal if some resources are listed under Failed resource Actions section, it happens when cluster is reconfigured/restarted.  
    Run following command to cleanup the Failed resource Actions

    $ `sudo pcs resource cleanup --all`  

    Check pcs status again to confirm that the resources are cleaned up from Failed resource Action section.

1.  The system is now ready for CSM on-boarding  
