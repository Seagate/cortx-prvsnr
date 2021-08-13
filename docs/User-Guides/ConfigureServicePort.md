# Configure the Service Port

These are the workaround steps to configure the service port on primary node (srvnode-1).
The service port could also be configured by mentioning the additional management port for primary node as shown [here](https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-Provisioner-CLI-Commands#configini-example) in the sample.

If the factory person misses to put in the additional management interface name in config.ini  during the factory install then following is the way to configure the service port manually: 
Note: Please run these steps on primary node: 

1. Configure the cluster pillar to have additional mgmt interface mentioned 
   First, check the current value of the management interface in cluster pillar:  

`[root@srvnode-1 ~]# salt srvnode-1 pillar.get cluster:srvnode-1:network:mgmt_nw:iface `  
`srvnode-1: `  
   `eno1 `   
`[root@srvnode-1 ~]#  `   


2. Update the pillar to have additional mgmt interface (eno2)  

`[root@srvnode-1 ~]# provisioner pillar_set cluster/srvnode-1/network/mgmt_nw/iface [\"eno1\",\ \"eno2\"]`  
`[root@srvnode-1 ~]# `  
  
3. Confirm the cluster pillar is updated with new interface: 

`[root@srvnode-1 ~]# salt srvnode-1 pillar.get cluster:srvnode-1:network:mgmt_nw:iface `  
`srvnode-1: `  
    `- eno1 `  
    `- eno2 `  
`[root@srvnode-1 ~]#` 
 
4. Run the following command to configure the eno1 as a support port.  

`[root@srvnode-1 ~]# salt srvnode-1 state.apply components.system.network.mgmt.support_port  `  
`[root@srvnode-1 ~]# `  

5. Check if IP 10.100.100.255 got assigned to the eno2 interface:  

 `3: eno2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN`  
 `group default qlen 1000 link/ether 3c:ec:ef:4a:96:01 brd`  
  `ff:ff:ff:ff:ff:ff inet 10.100.100.100/24 brd 10.100.100.255 scope global eno2 valid_lft forever preferred_lft forever `   


Once the IP is listed as shown above, please follow the section 9.1 of user guide to connect the laptop to eno2 port using ethernet cable.
