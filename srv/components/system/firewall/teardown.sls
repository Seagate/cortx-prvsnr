Remove public-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=public-data-zone

Remove private-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=private-data-zone

Remove management-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=management-zone

#TODO: 1. Use salt module to delete zone, if available.
#      2. Reset other rules set in components.system.firewall.config

Disable firewall:
  service.dead:
    - name: firewalld
    - enable: False

Remove firewall:
  pkg.purged:
<<<<<<< HEAD
    - name: firewall
=======
    - name: firewall
>>>>>>> 33947d93218e05157ec0f243850f12a3a218b918
