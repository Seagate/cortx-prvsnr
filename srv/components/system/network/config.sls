{# {% if pillar['cluster'][grains['id']]['network']['mgmt_nw']['ipaddr'] %}#}
# # Donot execute this block for DHCP settings on management network
{# {% if 'mgmt0' in grains['ip4_interfaces'] %}#}
{#   {% set mgmt_nw = 'mgmt0' %}#}
{# {% else %}#}
{#   {% set mgmt_nw = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] %}#}
{# {% endif %}#}
{#{% if pillar['cluster'][grains['id']]['network']['gateway_ip'] %}#}
# Network setup:
#   network.system:
#     - enabled: True
#     - hostname: {#{{ grains['fqdn'] }}#}
#     - apply_hostname: True
#     - gateway: {#{{ salt['pillar.get']("cluster:{0}:network:gateway_ip".format(grains['id']), grains['ip4_gw']) }}#}
#     - gatewaydev: {#{{ mgmt_nw }}#}
#     - require_reboot: True
{#{% else %}#}
# Network config failure:
#   test.fail_without_changes:
#     - name: Network configuration in absense of Gateway IP results in node inaccessibility.
{#{% endif %}#}
{# {% endif %}#}

Modify resolv.conf:
  file.managed:
    - name: /etc/resolv.conf
    - source: salt://components/system/network/files/resolv.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - replace: True
    - create: True
    - allow_empty: True

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

# Not requried
# Reboot system:
#   module.run:
#     - system.reboot: []
