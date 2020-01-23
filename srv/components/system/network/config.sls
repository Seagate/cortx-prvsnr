include:
  - components.system.network.install

# Disabling NetworkManager doesn't kill dhclient process.
# If not killed explicitly, it causes network restart to fail: COSTOR-439
Kill dhclient:
  cmd.run:
    - name: pkill -SIGTERM dhclient
    - onlyif: pgrep dhclient
    - requires:
      - service: Stop and disable NetworkManager service

{% if 'mgmt0' in grains['ip4_interfaces'] %}
  {% set mgmt_nw = 'mgmt0' %}
{% else %}
  {% set mgmt_nw = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] %}
{% endif %}
Network setup:
  network.system:
    - enabled: True
    - hostname: {{ grains['fqdn'] }}
    - apply_hostname: True
    - gateway: {{ salt['pillar.get']("cluster:{0}:network:gateway_ip".format(grains['id']), grains['ip4_gw']) }}
    - gatewaydev: {{ mgmt_nw }}
    - require_reboot: True
    - search: mero.colo.seagate.com

lo:
  network.managed:
    - name: lo
    - enabled: True
    - type: eth
    - nm_controlled: no
    - userctl: no
    - ipv6_autoconf: no
    - enable_ipv6: true
    - ipaddr: 127.0.0.1
    - netmask: 255.0.0.0
    - network: 127.0.0.0
    - broadcast: 127.255.255.255
