network:
  node_list:
    - eosnode-1
    - eosnode-2
  cluster_ip:                 # Unique IP address
  eosnode-1:
    mgmt_nw:                  # Management network interfaces
      iface:
        - eth0
      ipaddr:                 # to be set by DHCP
      netmask: 255.255.255.0
    data_nw:                  # Data network interfaces
      iface: 
        - eth1
      ipaddr: 192.16.0.1               # to be set by DHCP 
      netmask: 255.255.255.0
    floating_ip:
    gateway_ip:               # Gateway IP of network
  eosnode-2:
    is_primary: false
    mgmt_nw:                  # Management network interfaces
      iface:
        - eth0
      ipaddr: 
      netmask: 255.255.255.0
    data_nw:                  # Data network interfaces
      iface: 
        - eth1
      ipaddr: 192.16.0.2
      netmask: 255.255.255.0
    floating_ip:              # manual feed
    gateway_ip:               # Gateway IP of network