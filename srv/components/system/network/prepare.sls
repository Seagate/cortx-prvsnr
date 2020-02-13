Stop and disable NetworkManager service:
  service.dead:
    - name: NetworkManager
    - enable: False

Remove NetworkManager package:
  pkg.purged:
    - name: NetworkManager
    - require:
      - service: Stop and disable NetworkManager service

# Remove eth network interface configuration files:
#   cmd.run:
#     - name: rm -rf /etc/sysconfig/network-scripts/ifcfg-eth*
#     - onlyif: test -f /etc/sysconfig/network-scripts/ifcfg-eth0

Remove lan0:
  file.absent:
    - name: /etc/sysconfig/network-scripts/ifcfg-lan0
