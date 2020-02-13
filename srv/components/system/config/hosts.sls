#Set hostname:
#  cmd.run:
#    - name: hostnamectl set-hostname {{ pillar['cluster'][grains['id']]['hostname'] }}

hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1     localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1           localhost localhost.localdomain localhost6 localhost6.localdomain6
        -------------------------------------------------------------------------------
        {% set node_ip = set(pillar['cluster']['node_list']) - set(grains['id']) %}
        {%- if node_ip %}
        {% if 'mgmt0' in grains['ip4_interfaces'] -%}
        {{ salt['mine.get'](node_ip, 'mgmt_ip_addrs') }} {{ pillar['cluster'][node_ip]['hostname'] }}
        {% endif %}
        {% if ('data0' in grains['ip4_interfaces']) -%}
        {{ salt['mine.get'](node_ip, 'data_ip_addrs') }} {{ pillar['cluster'][node_ip]['hostname'] }}-data
        {% endif %}
        {% endif %}
    - user: root
    - group: root
