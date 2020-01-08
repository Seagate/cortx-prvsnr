{%- set mgmt_if = salt["pillar.get"]("cluster:{0}:network:mgmt_if".format(grains['id']), "lo") -%}

#Set hostname:
#  cmd.run:
#    - name: hostnamectl set-hostname {{ pillar['cluster'][grains['id']]['hostname'] }}

hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1    localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1          localhost localhost.localdomain localhost6 localhost6.localdomain6
        {{ grains["ip4_interfaces"][mgmt_if][0] }}    {{ grains['host'] }} {{ grains['fqdn'] }}
    - user: root
    - group: root
