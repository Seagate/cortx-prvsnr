#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

include:
  - .start

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

csm:
  firewalld.service:
    - name: csm
    - ports:
      - 28100/tcp
      - 28101/tcp
      - 28102/tcp
      - 28103/tcp

dhclient:
  firewalld.service:
    - name: dhclient
    - ports:
      - 68/udp

elasticsearch:
  firewalld.service:
    - name: elasticsearch
    - ports:
      - 9200/tcp
      - 9300/tcp

haproxy:
  firewalld.service:
    - name: haproxy

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

ntpd:
  firewalld.service:
    - name: ntpd
    - ports:
      - 123/udp

smtp:
  firewalld.service:
    - name: smtp
    - ports:
      - 25/tcp      # SMTP

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

openldap:
  firewalld.service:
    - name: openldap
    - ports:
      - 389/tcp     # over insecure channel
      # - 636/tcp     # over secure channel

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

saltmaster:
  firewalld.service:
    - name: saltmaster
    - ports:
      - 4505/tcp
      - 4506/tcp

uds:
  firewalld.service:
    - name: uds
    - ports:
      - 5000/tcp
      - 3535/tcp  #3535 & 4000 ports are used to expose websocket servers
      - 4000/tcp
      - 5125/udp  #UDS advertises remote volumes over UDP multicast over this port

www:
  firewalld.service:
    - ports:
      - 80/tcp
      - 443/tcp     # HTTPS

Add public data zone:
  cmd.run:
    - name: firewall-cmd --permanent --new-zone public-data-zone
    - unless: firewall-cmd --get-zones | grep public-data-zone
    - watch_in:
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
      - dhclient
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
      - dhclient
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
      - dhclient
      - hare
      - haproxy
      - high-availability
      - nfs
      - ssh
      - www
      - s3
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] }}
    # - rich_rules:
    #   - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
    - require:
      - Add public data zone
      - consul
      - dhclient
      - hare
      - haproxy
      - nfs
      - www
      - s3

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
    - default: True
    - prune_ports: True
    - prune_services: True
    - services:
      - consul
      - dhclient
      - csm
      - elasticsearch
      - ftp
      - high-availability
      - ntpd
      - openldap
      - smtp
      - rabbitmq
      - saltmaster
      - ssh
      - uds
      - www
      {% if salt['cmd.run']('rpm -qa glusterfs-server') %}
      - glusterfs
      {% endif %}
    - interfaces:
      - {{ mgmt_if }}
    - port_fwd:
      {% if pillar['cluster'][grains['id']]['is_primary'] %}
      - {{ pillar['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['storage_enclosure']['controller']['primary_mc']['ip'] }}
      {% else %}
      - {{ pillar['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['storage_enclosure']['controller']['secondary_mc']['ip'] }}
      {% endif %}
    - require:
      # - Add management zone
      - consul
      - dhclient
      - csm
      - elasticsearch
      - ntpd
      - openldap
      - smtp
      - rabbitmq
      - saltmaster
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
