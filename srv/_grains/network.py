import psutil

def netmask():
  interface_details = psutil.net_if_addrs()
  netmask = {}
  for iface in interface_details:
    netmask[iface]=interface_details[iface][0].netmask

  return {'ip4_netmask':netmask}

