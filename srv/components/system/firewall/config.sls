Public Zone:
  firewalld.present:
    - name: public
    - block_icmp:
      - echo-reply
      - echo-request
    - default: True
    - masquerade: True
    - ports:
      - 443/tcp
      - 123/udp
    - port_fwd:
      {% if pillar['cluster'][grains['id']]['is_primary'] %}
      - {{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['ip'] }}
      {% else %}
      - {{ pillar['cluster']['storage_enclosure']['controller']['primary_mc']['port'] }}:80:tcp:{{ pillar['cluster']['storage_enclosure']['controller']['secondary_mc']['ip'] }}
      {% endif %}
    - prune_services: False

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
      - 8008/tcp

mero:
  firewalld.service:
    - name: mero
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
      - 123/udp
      - 5161/tcp
      - 5162/tcp

s3:
  firewalld.service:
    - name: s3
    - ports:
      - 80/tcp
      - 8080/tcp
      - 443/tcp
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
      
add-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --new-zone data-zone
    - unless: firewall-cmd --zone=data-zone --list-all

add-management-zone:
  cmd.run:
    - name: firewall-cmd --permanent --new-zone management-zone
    - unless: firewall-cmd --zone=management-zone --list-all

data-zone:
  firewalld.present:
    - name: data-zone
    - services:
      - mero
      - nfs
      - s3
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['data_if'] }}
    - rich_rules:
        - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'

management-zone:
  firewalld.present:
    - name: management-zone
    - services:
      - saltmaster
      - csm
      - hare
      - sspl
      - others
      - ssh
    - interfaces:
      - {{ pillar['cluster'][grains['id']]['network']['mgmt_if'] }}
