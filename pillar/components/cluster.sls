cluster:
  type: single                      # single/ees/ecs
  node_list:                        # List of nodes to be managed as part of this cluster
    - eosnode-1                     # minion ID for node-1
  eosnode-1:                        # minion ID for node-1. Should match one from node_list above.
    hostname: eosnode-1
    is_primary: true
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
        port: 80
      secondary_mc:
        ip: 127.0.0.1
        port: 80
      user: user
      password: 'passwd'
