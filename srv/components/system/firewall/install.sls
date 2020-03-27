Install firewalld:
  pkg.installed:
    - name: firewalld

# Enable Firewalld
Unmask Firewall service:
  service.unmasked:
    - name: firewalld
    - require:
      - Install firewalld

# Ensure ssh works when the firwall servcie starts for the next time
{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}
Open public zone:
  firewalld.present:
    - name: public
    - default: True
    - ports:
      - 4505/tcp
      - 4506/tcp
    - prune_ports: False
    - services:
      - ssh
    - prune_services: False
    - prune_interfaces: False
    - require:
      - Ensure service running

Ensure service running:
  service.running:
    - name: firewalld
