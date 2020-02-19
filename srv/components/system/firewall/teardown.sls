Remove data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=data-zone

Remove management-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=management-zone

#TODO: 1. Use salt module to delete zone, if available.
#      2. Reset other rules set in components.system.firewall.config

Disable firewall:
  service.dead:
    - name: firewalld
    - enable: False
