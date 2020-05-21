{%- if (pillar['cluster'][node]['network']['mgmt_nw']['ipaddr']) and (not pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway']) %}
Management network config failure:
  test.fail_without_changes:
    - name: Static network configuration in absense of Gateway IP would result in node inaccessibility.
{% endif %}

{% set node = grains['id'] %}

Ensure bonding config for management bond:
  file.managed:
    - name: /etc/modprobe.d/bonding.conf
    - contents: options bonding max_bonds=0

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
    - defroute: yes
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
{% if pillar['cluster'][node]['network']['data_nw']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway'] }}
{% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

include:
  - components.system.network.config
