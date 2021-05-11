#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
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

dhserver:
  firewalld.service:
    - name: dhserver
    - ports:
      - 67/udp

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
      - 443/tcp     # HTTPS
      - 7081/tcp
      {% for port in range(8081, 8099) %}
      - {{ port }}/tcp
      {% endfor %}
      - 514/tcp
      - 514/udp
      - 8125/tcp
      - 6379/tcp
      # - 9080/tcp
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
      - 5125/udp  #UDS advertises remote volumes over UDP multicast over this port

www:
  firewalld.service:
    - ports:
      - 80/tcp

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
      - dhserver
      - haproxy
      - nfs
      - hare
      - high-availability
      - lnet
      - s3
      - uds
    - require:
      - Add public data zone
      - consul
      - dhclient
      - dhserver
      - haproxy
      - nfs
      - hare
      - lnet
      - s3
      - uds

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
      - dhserver
      - hare
      - haproxy
      - high-availability
      - nfs
      - ssh
      - uds
      {% if not 'physical' in grains['virtual'] %}
      - www                 # Open port 80 in public-data interface for OVA
      {% endif %}
      - s3
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] }}
    # - rich_rules:
    #   - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
    - require:
      - Add public data zone
      - consul
      - dhclient
      - dhserver
      - hare
      - haproxy
      - nfs
      - uds
      {% if not 'physical' in grains['virtual'] %}
      - www
      {% endif %}
      - s3

Private data zone:
  firewalld.present:
    - name: trusted
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }}
      - lo
    - default: False
    - masquerade: False
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False

{%- endif -%}

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{% endif %}

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
      - saltmaster
      - ssh
      - uds
      {% if salt['cmd.run']('rpm -qa glusterfs-server') %}
      - glusterfs
      {% endif %}
    - interfaces:
      - {{ mgmt_if }}
    {% if not 'physical' in grains['virtual'] %}
    - port_fwd:
      {% if pillar['cluster'][grains['id']]['is_primary'] %}
      - {{ pillar['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['storage_enclosure']['controller']['primary_mc']['ip'] }}
      {% else %}
      - {{ pillar['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['storage_enclosure']['controller']['secondary_mc']['ip'] }}
      {% endif %}
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
      - saltmaster
      - uds

Restart firewalld:
  module.run:
    - service.restart:
      - firewalld
