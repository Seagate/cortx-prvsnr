cluster:
  type: single                      # single/ees/ecs
  node_list:                        # List of nodes to be managed as part of this cluster
    - eosnode-1                     # minion ID for node-1 
    # - eosnode-2                     # minion ID for node-2
  eosnode-1:                        # minion ID for node-1. Should match one from node_list above.
    fqdn: eosnode-1
    is_primary: true
    network:
      mgmt_if: mgmt0                # Management network interfaces for bonding
      data_if: data0                # Management network interfaces for bonding
      gateway_ip: 10.0.2.2
    storage:
      metadata_device:              # Device for /var/mero and possibly SWAP
        # - dev/sdb
        - /dev/disk/by-path/pci-0000:00:16.0-sas-phy0-lun-0
      data_devices:                 # Data device/LUN from storage enclosure
        # - /dev/sdc
        - /dev/disk/by-path/pci-0000:00:16.0-sas-phy1-lun-0
  eosnode-2:                        # minion ID for node-2. Should match one from node_list above.
    fqdn: eosnode-2
    is_primary: false
    network:
      mgmt_if: mgmt0                # Management network interfaces for bonding
      data_if: data0                # Management network interfaces for bonding
      gateway_ip: 10.0.2.2
    storage:
      metadata_device:              # Device for /var/mero and possibly SWAP
        - /dev/disk/by-path/pci-0000:00:16.0-sas-phy0-lun-0
        # - dev/sdb
      data_devices:                 # Data device/LUN from storage enclosure
        - /dev/disk/by-path/pci-0000:00:16.0-sas-phy1-lun-0
        # - /dev/sdc
  storage_enclosure:
    id: storage_node_1            # equivalent to fqdn for server node
    type: 5U84                    # Type of enclosure. E.g. 5U84/PODS
    controller:
      type: gallium               # Type of controller on storage node. E.g. gallium/indium/sati
      primary_mc:
        ip: 127.0.0.1
        port: 80
      secondary_mc:  
        ip: 127.0.0.1
        port: 80
      user: user
      password: 'passwd'
