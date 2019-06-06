{% set node_name = salt['pillar.get'] ('node_name') %}

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

salt_disable_firewalld:
  service.dead:
    - name: firewalld
    - enable: False

set_hostname:
  cmd.run:
    - name: hostnamectl set-hostname {{ node_name }}

# set_nic_bios_dev_name_grub:
#   file.replace:
#     - name: /etc/default/grub
#     - pattern: 'biosdevname=0'
#     - repl: 'biosdevname=1'
#     - append_if_not_found: False
#     - prepend_if_not_found: False
#     - ignore_if_missing: True

# set_nic_net_if_name_grub:
#   file.replace:
#     - name: /etc/default/grub
#     - pattern: 'net.ifnames=0'
#     - repl: 'net.ifnames=1'
#     - append_if_not_found: False
#     - prepend_if_not_found: False
#     - ignore_if_missing: True

remove_eth_cfg_files:
  cmd.run:
    - name: rm -rf /etc/sysconfig/network-scripts/ifcfg-eth*
    - onlyif: test -f /etc/sysconfig/network-scripts/ifcfg-eth0

system:
  network.system:
    - enabled: True
    - hostname: {{ node_name }}
    - apply_hostname: True
    - gateway: {{ pillar['facts'][node]['gateway_ip'] }}
    - require_reboot: True

# set_network_file:
#   file.managed:
#     - name: /etc/sysconfig/network
#     - source: salt://components/system/files/etc/sysconfig/network
#     - dir_mode: 0644
#     - file_mode: 0644
#     - clean: False
#     - keep_symlinks: True
#     - include_empty: True
#     - watch_in:
#       - service: service_network

# set_network_script_files:
#   file.recurse:
#     - name: /etc/sysconfig/network-scripts
#     - source: salt://build_node/files/etc/sysconfig/network-scripts
#     - keep_source: False
#     - dir_mode: 0644
#     - file_mode: 0644
#     - clean: False
#     - keep_symlinks: True
#     - include_empty: True

{% set network_ifs = salt['grains.get']('ip_interfaces' ,'') %}
{% for nw_id,nw_if in network_ifs.items() %}
{% if 'lo' not in nw_id and 'em' not in nw_id %}
# Setup network for eth* interfaces
{{ nw_id }}:
  network.managed:
    - device: {{ nw_id }}
    - enabled: True
    - proto: none
    - nm_controlled: no
    - userctl: no
    - slave: yes
    - MASTER: data0
{% endif %}
{% endfor %}

rm_ifcfg_lan0:
  file.absent:
    - name: /etc/sysconfig/network-scripts/ifcfg-lan0

set_bonding_config:
  file.managed:
    - name: /etc/modprobe.d/bonding.conf
    - mode: 0644
    - contents: options bonding max_bonds=0

Setup mgmt0 bonding:
  network.managed:
      - name: mgmt0
      - type: bond
      - enabled: True
      - proto: dhcp
      - nm_controlled: no
      - userctl: no
      # - slaves: em1 em2
      - mtu: 1500
      - mode: 802.3ad
      - miimon: 100
      - lacp_rate: fast
      - xmit_hash_policy: layer2+3

Setup data0 bonding:
  network.managed:
      - name: data0
      - type: bond
      - enabled: True
      - proto: dhcp
      - nm_controlled: no
      - userctl: no
      - mtu: 9000
      # - slaves: p1p1 p1p2
      - mode: 802.3ad
      - miimon: 100
      - lacp_rate: fast
      - xmit_hash_policy: layer2+3

service_network:
  service.running:
    - name: network.service
    - watch:
      - rm_ifcfg_lan0
      - kill_dhclient

# reboot_node:
#   module.run:
#     - name: system.reboot
#     - onlyif: test -f /root/os_flash.done
