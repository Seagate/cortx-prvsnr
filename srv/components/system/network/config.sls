include:
  - components.system.network.install

{% set node = grains['id'] %}
# Disabling NetworkManager doesn't kill dhclient process.
# If not killed explicitly, it causes network restart to fail: COSTOR-439
Kill dhclient:
  cmd.run:
    - name: pkill -SIGTERM dhclient
    - onlyif: pgrep dhclient
    - requires:
      - service: Stop and disable NetworkManager service

Network setup:
  network.system:
    - enabled: True
    - hostname: {{ grains['fqdn'] }}
    - apply_hostname: True
    - gateway: {{ pillar['cluster'][node]['network']['gateway_ip'] }}
    - require_reboot: True

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
