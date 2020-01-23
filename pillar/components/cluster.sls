cluster:
  type: single                      # single/ees/ecs
  node_list:                        # List of nodes to be managed as part of this cluster
    - eosnode-1                     # minion ID for node-1
  eosnode-1:                        # minion ID for node-1. Should match one from node_list above.
    hostname: eosnode-1
    is_primary: true
    network:
      mgmt_nw:                  # Management network interfaces
        iface:
          - eth0
        ipaddr: 
        netmask: 
      data_nw:                  # Data network interfaces
        iface: 
          - eth1
        ipaddr: 172.19.10.101
        netmask: 
      gateway_ip:               # Gateway IP of network
    storage:
      metadata_device:              # Device for /var/mero and possibly SWAP
        - /dev/sdb
      data_devices:                 # Data device/LUN from storage enclosure
        - /dev/sdc
  storage_enclosure:
    id: storage_node_1            # equivalent to fqdn for server node
    type: 5U84                    # Type of enclosure. E.g. 5U84/PODS
    controller:
      type: gallium               # Type of controller on storage node. E.g. gallium/indium/sati
      primary_mc:
        ip: 127.0.0.1
        port: 8090
      secondary_mc:
        ip: 127.0.0.1
        port: 8090
      user: user
      password: 'passwd'
