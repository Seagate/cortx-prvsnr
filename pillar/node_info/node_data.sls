mine_functions:
  mgmt_ip:
    - mine_function: grains.get
    - ip4_interfaces:mgmt0:0
  data_ip:
    - mine_function: grains.get
    - ip4_interfaces:data0:0
  hostname:
    - mine_function: grains.get
    - host
  fqdn:
    - mine_function: grains.get
    - fqdn
