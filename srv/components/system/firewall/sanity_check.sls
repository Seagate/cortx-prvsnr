{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
{%- endif -%}
{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}

Verify NIC opened for management-zone:
  cmd.run:
    - name: firewall-cmd --permanent --zone=management-zone --list-interfaces | grep {{ mgmt_if }}

Verify NIC opened for data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --zone=data-zone --list-interfaces | grep {{ data_if }}

Verify saltmaster ports:
  cmd.run:
    - name: firewall-cmd --permanent --service saltmaster --get-ports | grep -P '(?=.*?4505/tcp)(?=.*?4506/tcp)^.*$'

Verfiy csm ports:
  cmd.run:
    - name: firewall-cmd --permanent --service csm --get-ports | grep -P '(?=.*?8100/tcp)(?=.*?8101/tcp)(?=.*?8102/tcp)(?=.*8103/tcp)^.*$'

Verify hare ports:
  cmd.run:
    - name: firewall-cmd --permanent --service hare --get-ports | grep -P '(?=.*?8300/tcp)(?=.*?8301/tcp)(?=.*?8302/tcp)(?=.*?8008/tcp)(?=.*?8500/tcp)^.*$'

Verify lnet ports:
  cmd.run:
    - name: firewall-cmd --permanent --service lnet --get-ports | grep -P '(?=.*?988/tcp)^.*$'

Verify nfs ports:
  cmd.run:
    - name: firewall-cmd --permanent --service nfs --get-ports | grep -P '(?=.*?2049/tcp)(?=.*?2049/udp)(?=.*?32803/tcp)(?=.*?892/tcp)(?=.*?875/tcp)^.*$'

Verify s3 ports:
  cmd.run:
    - name: firewall-cmd --permanent --service s3 --get-ports | grep -P '(?=.*?80/tcp)(?=.*?8080/tcp)(?=.*?443/tcp)(?=.*?7081/tcp)(?=.*?514/tcp)(?=.*?8125/tcp)(?=.*?6379/tcp)(?=.*?9080/tcp)(?=.*?9443/tcp)(?=.*?9086/tcp)(?=.*?389/tcp)(?=.*?636/tcp)(?=.*?80(8[1-9]))(?=.*?80(9[0-9]))^.*$'

Verify sspl ports:
  cmd.run:
    - name: firewall-cmd --permanent --service sspl --get-ports | grep -P '(?=.*?8090/tcp)^.*$'
