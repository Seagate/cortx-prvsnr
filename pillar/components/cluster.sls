cluster:
  cluster_ip:                         # Cluster IP for HAProxy
  pvt_data_nw_addr: 192.168.0.0
  mgmt_vip:                           # Management VIP for CSM
  search_domains:                     # Do not update
  dns_servers:                        # Do not update
  type: dual                           # single/dual/cluster
  node_list:
    - srvnode-1
    - srvnode-2
  srvnode-1:
    hostname: srvnode-1
    is_primary: true
    bmc:
      ip:
      user: ADMIN
      secret: 'adminBMC!'
    network:
      mgmt_nw:                        # Management network interfaces
        iface:
          - eno1
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
        gateway:                   # Gateway IP of Management Network. Not requried for DHCP.
      data_nw:                        # Data network interfaces
        iface:
          - enp175s0f0                # Public Data
          - enp175s0f1                # Private Data (direct connect)
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
        gateway:                   # Gateway IP of Public Data Network. Not requried for DHCP.
        pvt_ip_addr: 192.168.0.1      # Fixed IP of Private Data Network
        roaming_ip: 192.168.0.3       # Applies to private data network
    storage:
      metadata_device:                # Device for /var/mero and possibly SWAP
        - /dev/sdb                    # Auto-populated by components.system.storage.multipath
      data_devices:                   # Data device/LUN from storage enclosure
        - /dev/sdc                    # Auto-populated by components.system.storage.multipath
  srvnode-2:
    hostname: srvnode-2
    is_primary: false
    bmc:
      ip:
      user: ADMIN
      secret: 'adminBMC!'
    network:
      mgmt_nw:                        # Management network interfaces
        iface:
          - eno1
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
        gateway:                   # Gateway IP of Management Network. Not requried for DHCP.
      data_nw:                        # Data network interfaces
        iface:
          - enp175s0f0                # Public Data
          - enp175s0f1                # Private Data (direct connect)
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
        gateway:                   # Gateway IP of Public Data Network. Not requried for DHCP.
        pvt_ip_addr: 192.168.0.2      # Fixed IP of Private Data Network
        roaming_ip: 192.168.0.4       # Applies to private data network
    storage:
      metadata_device:              # Device for /var/mero and possibly SWAP
        - /dev/sdb
      data_devices:                 # Data device/LUN from storage enclosure
        - /dev/sdc
