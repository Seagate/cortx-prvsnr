{% if salt['service.running']('firewalld') %}

# Ensure ssh works when the firwall servcie starts for the next time
{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}
public:
  firewalld.present:
    - name: trusted
    - default: True
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False
    - require:
      - Start and enable firewalld service

Remove public-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=public-data-zone
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service
      - public
    - watch_in:
      - Stop and disable Firewalld service

{% if not ('data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0']) %}
Remove public data interfaces:
  cmd.run:
    - name: firewall-cmd --remove-interface=data --zone=public-data-zone --permanent
{% else %}
Remove public and private data interfaces:
  cmd.run:
    - names: 
      - firewall-cmd --remove-interface={{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] }} --zone=public-data-zone --permanent
      - firewall-cmd --remove-interface={{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }} --zone=private --permanent
{% endif %}

#{% if not ('data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0']) %}
# Remove private-data-zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --delete-zone=private-data-zone
#     - onlyif: firewall-cmd --get-zones | grep private-data-zone
#     - require:
#       - Start and enable firewalld service
#       - public
#     - watch_in:
#       - Stop and disable Firewalld service
#{% endif %}

# Remove management-zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --delete-zone=management-zone
#     - onlyif: firewall-cmd --get-zones | grep management-zone
#     - require:
#       - Start and enable firewalld service
#       - public
#     - watch_in:
#       - Stop and disable Firewalld service

include:
  - .stop
{% endif %}
