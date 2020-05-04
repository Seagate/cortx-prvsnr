{% set node = grains['id'] %}
Ensure bonding config for data bond:
  file.managed:
    - name: /etc/modprobe.d/bonding.conf
    - content: options bonding max_bonds=0

# Setup network for data interfaces
{% for iface in pillar['cluster'][node]['network']['data_nw']['iface'] %}
{{ iface }}:
  network.managed:
    - device: {{ iface }}
    - enabled: True
    - type: slave
    - master: data0
    - requires_in:
      - Setup data0 bonding
    - watch_in:
      - Shutdown {{ iface }}

Shutdown {{ iface }}:
  cmd.run:
    - name: ifdown {{ iface }}
    - onlyif: '[ "up" == "$(cat /sys/class/net/{{iface}}/operstate)" ]'
{% endfor %}

Setup data0 bonding:
  network.managed:
    - name: data0
    - type: bond
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - mtu: 9000
    - defroute: no
    - mode: 802.3ad
    - miimon: 100
    - lacp_rate: fast
    - xmit_hash_policy: layer2+3
{% if pillar['cluster'][node]['network']['data_nw']['ipaddr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data_nw']['ipaddr'] }}
{% if pillar['cluster'][node]['network']['data_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data_nw']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['data_nw']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['data_nw']['gateway'] }}
{% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

