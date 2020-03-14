{% set node = grains['id'] %}

# Setup network for data interfaces
Public direct network:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['data_nw']['iface'][0] }}
    - device: {{ pillar['cluster'][node]['network']['data_nw']['iface'][0] }}
    - type: eth
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - onboot: yes
    - userctl: no
    - mtu: 9000
{% if pillar['cluster'][node]['network']['data_nw']['ipaddr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data_nw']['ipaddr'] }}
{% if pillar['cluster'][node]['network']['data_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data_nw']['netmask'] }}
{%- endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

{% set pvt_nw = pillar['cluster']['pvt_data_nw_addr'] %}
{% set pvt_ip = ("{0}.{1}").format('.'.join(pvt_nw.split('.')[:3]), grains['id'].split('-')[1]) %}
Private direct network:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['data_nw']['iface'][1] }}
    - device: {{ pillar['cluster'][node]['network']['data_nw']['iface'][1] }}
    - type: eth
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - mtu: 9000
    - onboot: yes
    - userctl: no
    - netmask: 255.255.255.0
    - proto: none
    - ipaddr: {{ pvt_ip }}

{% if pillar['cluster'][grains['id']]['is_primary'] %}
Update roaming IPs in cluster.sls pillar:
  module.run:
    - saltutil.sync_all: []
    - saltutil.refresh_modules: []
    - cluster.nw_roaming_ip: []
    - saltutil.refresh_pillar: []
{% endif %}
