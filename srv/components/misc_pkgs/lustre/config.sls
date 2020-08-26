{%- if 'lo' in pillar['cluster'][grains['id']]['network']['data_nw'] %}
Update lnet config file:
  test.fail_without_changes:
    - name: LNet doesn't support loopback network interface. Config dropped.

{% else %}
{%- if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] -%}
{%- endif -%}

Update lnet config file:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
{% if salt['cmd.run']('lspci -d"15b3:*"') %}
      - options lnet networks=o2ib({{ data_if }})  config_on_load=1  lnet_peer_discovery_disabled=1
{% else %}
      - options lnet networks=tcp({{ data_if }})  config_on_load=1  lnet_peer_discovery_disabled=1
{% endif %}
    - user: root
    - group: root

{% endif %}
