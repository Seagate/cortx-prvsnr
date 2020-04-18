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
