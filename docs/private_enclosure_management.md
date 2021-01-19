#  Configuring Management Interface On Server Node

1.  Modify interface configuration files on both nodes as under:  
    srvnode_1: `/etc/sysconfig/network-scripts/ifcfg-eno2`  
    ```  
    TYPE=Ethernet
    PROXY_METHOD=none
    BROWSER_ONLY=no
    BOOTPROTO=none
    DEFROUTE=no
    IPV4_FAILURE_FATAL=no
    IPV6INIT=no
    IPV6_DEFROUTE=no
    IPV6_FAILURE_FATAL=no
    IPV6_ADDR_GEN_MODE=stable-privacy
    DEVICE=eno2
    ONBOOT=yes
    IPADDR=10.0.0.4
    NETMASK=255.255.255.0
    ```  

    srvnode_2: `/etc/sysconfig/network-scripts/ifcfg-eno2`  
    ```  
    TYPE=Ethernet
    PROXY_METHOD=none
    BROWSER_ONLY=no
    BOOTPROTO=none
    DEFROUTE=no
    IPV4_FAILURE_FATAL=no
    IPV6INIT=no
    IPV6_DEFROUTE=no
    IPV6_FAILURE_FATAL=no
    IPV6_ADDR_GEN_MODE=stable-privacy
    DEVICE=eno2
    ONBOOT=yes
    IPADDR=10.0.0.5
    NETMASK=255.255.255.0
    ```  

1.  Restart the 1GBps interface with direct cable connection to Enclosure ethernet port  
    E.g. For eno1 one must run commands:  
    ```  
    ifdown eno-2  
    ifup eno-2  
    ```  

1.  Verify the IP assignment with command:  
    ```  
    ip a  
    ```  
    Note: Look for the same network interface that was configured in #1  


# Configure Static IP On Storage Enclosure

Follow step #2 from guide: https://github.com/Seagate/cortx-prvsnr/wiki/In-band-Setup#RBOD-side
