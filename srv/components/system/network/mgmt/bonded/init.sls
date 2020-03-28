{%- if pillar['cluster'][grains['id']]['network']['gateway_ip'] %}
{% set node = grains['id'] %}

# Setup network for management interfaces
{% for iface in pillar['cluster'][node]['network']['mgmt_nw']['iface'] %}
{{ iface }}:
  network.managed:
    - device: {{ iface }}
    - enabled: True
    - type: slave
    - master: mgmt0

Shutdown {{ iface }}:
  cmd.run:
    - name: ifdown {{ iface }}
    - onlyif: '[ "up" == "$(cat /sys/class/net/{{iface}}/operstate)" ]'
{% endfor %}

Setup mgmt0 bonding:
  network.managed:
    - name: mgmt0
    - type: bond
    - enabled: True
    - nm_controlled: no
    - userctl: no
    # - slaves: em1 em2
    - mtu: 1500
    - mode: active-backup
    - miimon: 100
{% if pillar['cluster'][node]['network']['mgmt_nw']['ipaddr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['mgmt_nw']['ipaddr'] }}
{% if pillar['cluster'][node]['network']['data_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data_nw']['netmask'] }}
{%- endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

include:
  - components.system.network.config

{% else %}
Management network config failure:
  test.fail_without_changes:
    - name: Network configuration in absense of Gateway IP results in node inaccessibility.
{% endif %}