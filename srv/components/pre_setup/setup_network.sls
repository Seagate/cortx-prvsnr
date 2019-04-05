{% set bmc_port1_mac_safe = salt['grains.get']('bmc_network:port1_mac_safe') %}

{% set node_name = salt['pillar.get'] ('node:{0}:hostname'.format(bmc_port1_mac_safe)) %}

set_hostname:
  cmd.run:
    - name: hostnamectl set-hostname {{ node_name }}

stop_and_diasble_nm:
  service.dead:
    - name: NetworkManager
    - enable: False

purge_package_nm:
  pkg.purged:
    - name: NetworkManager
    - require:
      - service: stop_and_diasble_nm

# Disabling NetworkManager doesn't kill dhclient process.
# If not killed explicitly, it causes network restart to fail: COSTOR-439
kill_dhclient:
  cmd.run:
    - name: pkill -SIGTERM dhclient
    - unless: pgrep dhclient
    - watch:
      - service: stop_and_diasble_nm
    - require_in:
      - service: service_network

salt_disable_firewalld:
  service.dead:
    - name: firewalld
    - enable: False

rm_ifcfg_lan0:
  file.absent:
    - name: /etc/sysconfig/network-scripts/ifcfg-lan0

set_network_file:
  file.managed:
    - name: /etc/sysconfig/network
    - source: salt://build_node/files/etc/sysconfig/network
    - dir_mode: 0644
    - file_mode: 0644
    - clean: False
    - keep_symlinks: True
    - include_empty: True
      - watch_in:
          - service: service_network

service_network:
  service.running:
    - name: network.service
