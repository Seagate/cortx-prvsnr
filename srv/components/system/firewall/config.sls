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

hare:
  firewalld.service:
    - name: hare
    - ports:
      - 8500/tcp
      - 8300/tcp
      - 8301/tcp
      - 8302/tcp
      - 8301/udp
      - 8302/udp
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

others:
  firewalld.service:
    - name: others
    - ports:
      - 5161/tcp
      - 5162/tcp
      - 443/tcp

haproxy:
  firewalld.service:
    - name: haproxy
    - ports:
      - 80/tcp
      - 8080/tcp
      - 443/tcp

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

# Not required, watch triggers reload
#Stop Firewald:
#  service.dead:
#    - name: firewalld
#    - watch:
#      - Stop Firewald

Start and enable firewalld:
  service.running:
    - name: firewalld
    - enable: True
    - reload: True

Add public data zone:
<<<<<<< HEAD
  cmd.run:
    - name: firewall-cmd --permanent --new-zone public-data-zone
    - watch_in:
      - Start and enable firewalld

Add private data zone:
  cmd.run:
=======
  cmd.run:
    - name: firewall-cmd --permanent --new-zone public-data-zone
    - watch_in:
      - Start and enable firewalld

Add private data zone:
  cmd.run:
>>>>>>> EOS-5962: Direct network config.
    - name: firewall-cmd --permanent --new-zone private-data-zone
    - watch_in:
      - Start and enable firewalld

Add management zone:
  cmd.run:
    - name: firewall-cmd --permanent --new-zone management-zone
    - watch_in:
      - Start and enable firewalld

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
{%- endif -%}
Public data zone:
  firewalld.present:
    - name: public-data-zone
    - default: True
    - services:
      - haproxy
      - nfs
      - s3
    - interfaces:
      - {{ data_if }}
    - rich_rules:
      - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
    - require:
<<<<<<< HEAD
      - Add public data zone
=======
      - Add data zone
>>>>>>> EOS-5962: Direct network config.
      - haproxy
      - nfs
      - s3

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] -%}
{%- endif -%}
Private data zone:
  firewalld.present:
    - name: private-data-zone
    - default: True
    - services:
      - hare
      - lnet
    - interfaces:
      - {{ data_if }}
    - rich_rules:
      - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
    - require:
<<<<<<< HEAD
      - Add private data zone
=======
      - Add data zone
>>>>>>> EOS-5962: Direct network config.
      - hare
      - lnet

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}
Management zone:
  firewalld.present:
    - name: management-zone
    - default: True
    - services:
      - ntpd
      - saltmaster
      - csm
      - sspl
      - others
      - ssh
      - high-availability
    - interfaces:
      - {{ mgmt_if }}
    - port_fwd:
      {% if pillar['cluster'][grains['id']]['is_primary'] %}
      - {{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['ip'] }}
      {% else %}
      - {{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['cluster']['storage_enclosure']['controller']['secondary_mc']['ip'] }}
      {% endif %}
    - require:
      - Add management zone
      - ntpd
      - saltmaster
      - csm
      - sspl
      - others

Public Zone:
  firewalld.present:
    - name: public
    - block_icmp:
      - echo-reply
      - echo-request
    - masquerade: True
    - prune_services: False
    - prune_ports: True
    - prune_interfaces: True
    - require:
      - Add management zone
