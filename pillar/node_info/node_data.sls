mine_functions:
  data_ip_addrs:
    - mine_function: network.ip_addrs
    - eth1
  mgmt_ip_addrs:
    - mine_function: network.ip_addrs
    - eth0
  bmc_ip:
    mine_function: grains.get
    key: bmc_ip

  # mgmt_ip:
  #   - mine_function: grains.get
  #   - ip4_interfaces:mgmt0:0
  # data_ip:
  #   - mine_function: grains.get
  #   - ip4_interfaces:data0:0
  # hostname:
  #   - mine_function: grains.get
  #   - host
  # fqdn:
  #   - mine_function: grains.get
  #   - fqdn
