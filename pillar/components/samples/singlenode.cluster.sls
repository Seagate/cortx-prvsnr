cluster:
  cluster_ip:
  pvt_data_nw_addr: 192.168.0.0
  search_domains:                     # Do not update
  dns_servers:                        # Do not update
  type: single        # single/ees/ecs
  node_list:
    - eosnode-1
  eosnode-1:
    hostname: eosnode-1
    is_primary: true
    network:
      mgmt_nw:                  # Management network interfaces
        iface:
          - eth0
        ipaddr: 
        netmask: 255.255.252.0
      data_nw:                  # Data network interfaces
        iface: 
          - eth1
        ipaddr: 
        netmask: 255.255.0.0
        pvt_ip_addr: 192.168.0.1      # Fixed IP of Private Data Network 
        roaming_ip: 192.168.0.3       # Applies to private data network
      floating_ip:
      gateway_ip:               # Gateway IP of network
    storage:
      metadata_device:                # Device for /var/mero and possibly SWAP
        - /dev/sdb
      data_devices:                   # Data device/LUN from storage enclosure
        - /dev/sdc
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
