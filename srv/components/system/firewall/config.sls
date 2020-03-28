include:
  - .start

ntpd:
  firewalld.service:
    - name: ntpd 
    - ports:
      - 123/udp

saltmaster:
  firewalld.service:
    - name: saltmaster
    - ports:
      - 4505/tcp
      - 4506/tcp

csm:
  firewalld.service:
    - name: csm
    - ports:
      - 8100/tcp
      - 8101/tcp
      - 8102/tcp
      - 8103/tcp

consul:
  firewalld.service:
    - name: consul
    - ports:
      - 8600/tcp
      - 8600/udp
      - 8500/tcp
      - 8301/tcp
      - 8301/udp
      - 8302/tcp
      - 8302/udp
      - 8300/tcp

hare:
  firewalld.service:
    - name: hare
    - ports:
      - 8008/tcp

lnet:
  firewalld.service:
    - name: lnet
    - ports:
      - 988/tcp

nfs:
  firewalld.service:
    - name: nfs
    - ports:
      - 2049/tcp
      - 2049/udp
      - 32803/tcp
      - 892/tcp
      - 875/tcp

rabbitmq:
  firewalld.service:
    - name: rabbitmq
    - ports:
      - 4369/tcp          # epmd
      - 5671/tcp          # AMQP 0-9-1 and 1.0 clients without and with TLS
      - 5672/tcp          # AMQP 0-9-1 and 1.0 clients without and with TLS
      - 25672/tcp         # inter-node and CLI tools communication
{% for port in range(35672,35682) %}
      - {{ port }}/tcp    # CLI tools (Erlang distribution client ports) for communication with nodes
{% endfor %}
      - 15672/tcp         #  HTTP API clients, management UI and rabbitmqadmin

uds:
  firewalld.service:
    - name: uds
    - ports:
      - 5000/tcp

others:
  firewalld.service:
    - name: others
    - ports:
      - 25/tcp      # SMTP

www:
  firewalld.service:
    - ports:
      - 80/tcp
      - 443/tcp     # HTTPS

haproxy:
  firewalld.service:
    - name: haproxy

s3:
  firewalld.service:
    - name: s3
    - ports:
      - 7081/tcp
      {% for port in range(8081, 8099) %}
      - {{ port }}/tcp
      {% endfor %}
      - 514/tcp
      - 514/udp
      - 8125/tcp
      - 6379/tcp
      - 9080/tcp
      - 9443/tcp
      - 9086/tcp
      - 389/tcp
      - 636/tcp

sspl:
  firewalld.service:
    - name: sspl
    - ports:
      - 8090/tcp

Add public data zone:
  cmd.run:
    - name: firewall-cmd --permanent --new-zone public-data-zone
    - unless: firewall-cmd --get-zones | grep public-data-zone
    - listen_in:
      - Start and enable firewalld service

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
Data-zone:
  firewalld.present:
    - name: public-data-zone
    - interfaces:
      - data0
    - default: False
    - prune_ports: True
    - prune_services: True
    - prune_interfaces: True
    - services:
      - consul
      - haproxy
      - nfs
      - hare
      - high-availability
      - lnet
      - s3
      - www
    - require:
      - Add public data zone
      - consul
      - haproxy
      - nfs
      - hare
      - lnet
      - s3
      - www

# No restrictions for localhost
Localhost:
  firewalld.present:
    - name: trusted
    - interfaces:
      - lo
    - sources:
      - 127.0.0.0/24
    - default: False
    - masquerade: False
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False

{% else %}
Public data zone:
  firewalld.present:
    - name: public-data-zone
    - default: False
    - prune_ports: True
    - prune_services: True
    - prune_interfaces: True
    - services:
      - consul
      - hare
      - haproxy
      - nfs
      - www
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] }}
    # - rich_rules:
    #   - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
    - require:
      - Add public data zone
      - consul
      - hare
      - haproxy
      - nfs
      - www

Private data zone:
  firewalld.present:
    - name: trusted
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }}
    - default: False
    - sources:
      - 127.0.0.0/24
      - 192.168.0.0/16
    - masquerade: False
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False

# Add private data zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --new-zone private-data-zone
#     - unless: firewall-cmd --get-zones | grep private-data-zone
#     - watch_in:
#       - Start and enable firewalld service

# Private data zone:
#   firewalld.present:
#     - name: private-data-zone
#     - default: False
#     - prune_ports: True
#     - prune_services: True
#     - prune_interfaces: True
#     - services:
#       - hare
#       - high-availability
#       - lnet
#       - s3
#     - interfaces:
#       - {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }}
#     # - rich_rules:
#     #   - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
#     - require:
#       - Add private data zone
#       - hare
#       - lnet
#       - s3
{%- endif -%}

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{% endif %}
# Add management zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --new-zone management-zone
#     - unless: firewall-cmd --get-zones | grep management-zone
#     - watch_in:
#       - Start and enable firewalld service

Management zone:
  firewalld.present:
    - name: public
    - block_icmp:
      - echo-reply
      - echo-request
    - default: True
    - prune_ports: True
    - prune_services: True
    - services:
      - high-availability
      - consul
      - csm
      - ntpd
      - saltmaster
      - sspl
      - rabbitmq
      - others
      - ssh
      - uds
      - www
    - interfaces:
      - {{ mgmt_if }}
    - port_fwd:
      {% if pillar['cluster'][grains['id']]['is_primary'] %}
      - {{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['ip'] }}
      {% else %}
      - {{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['cluster']['storage_enclosure']['controller']['secondary_mc']['ip'] }}
      {% endif %}
    - require:
      # - Add management zone
      - consul
      - csm
      - ntpd
      - saltmaster
      - sspl
      - rabbitmq
      - others
      - uds
      - www

# Public Zone:
#   firewalld.present:
#     - name: public
#     - block_icmp:
#       - echo-reply
#       - echo-request
#     - masquerade: True
#     - prune_services: False
#     - prune_ports: True
#     - prune_interfaces: True
#     - require:
#       - Public data zone
#       - Management zone
#     - watch_in:
#       - service: Start and enable firewalld service

Restart firewalld:
  module.run:
    - service.restart:
      - firewalld
