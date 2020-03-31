cluster:
  cluster_ip:                         # Cluster IP for HAProxy
  pvt_data_nw_addr: 192.168.0.0
  mgmt_vip:                           # Management VIP for CSM
  search_domains:
    - pun.seagate.com
    - colo.seagate.com
    - eos.colo.seagate.com
  dns_servers:
    - 10.237.10.253
    - 10.237.10.254
    - 10.230.240.51
    - 10.230.240.52
  type: ees                           # single/ees/ecs
  node_list:
    - eosnode-1
    - eosnode-2
  eosnode-1:
    hostname: eosnode-1
    is_primary: true
    network:
      mgmt_nw:                        # Management network interfaces
        iface:
          - eno1
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
      data_nw:                        # Data network interfaces
        iface:
          - enp175s0f0                      # Public Data
          - enp175s0f1                      # Private Data (direct connect)
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
        pvt_ip_addr: 192.168.0.1      # Fixed IP of Private Data Network 
        roaming_ip: 192.168.0.3       # Applies to private data network
      gateway_ip:                     # Gateway IP of network. Not requried for DHCP.
    storage:
      metadata_device:                # Device for /var/mero and possibly SWAP
        - /dev/sdb                    # Auto-populated by components.system.storage.multipath
      data_devices:                   # Data device/LUN from storage enclosure
        - /dev/sdc                    # Auto-populated by components.system.storage.multipath
  eosnode-2:
    hostname: eosnode-2
    is_primary: false
    network:
      mgmt_nw:                        # Management network interfaces
        iface:
          - eno1
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
      data_nw:                        # Data network interfaces
        iface:
          - enp175s0f0                      # Public Data
          - enp175s0f1                      # Private Data (direct connect)
        ipaddr:                       # DHCP is assumed if left blank
        netmask: 255.255.0.0
        pvt_ip_addr: 192.168.0.2      # Fixed IP of Private Data Network
        roaming_ip: 192.168.0.4       # Applies to private data network
      gateway_ip:                     # Gateway IP of network. Not requried for DHCP.
    storage:
      metadata_device:                # Device for /var/mero and possibly SWAP
        - /dev/sdb                    # Auto-populated by components.system.storage.multipath
      data_devices:                   # Data device/LUN from storage enclosure
        - /dev/sdc                    # Auto-populated by components.system.storage.multipath
  storage_enclosure:
    id: storage_node_1            # equivalent to fqdn for server node
    type: 5U84                    # Type of enclosure. E.g. 5U84/PODS
    controller:
      type: gallium               # Type of controller on storage node. E.g. gallium/indium/sati
      primary_mc:
        ip: 10.0.0.2
        port: 80
      secondary_mc:
        ip: 10.0.0.3
        port: 80
      user: manage
      secret: 'passwd'
