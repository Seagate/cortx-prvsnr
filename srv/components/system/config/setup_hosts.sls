#Set hostname:
#  cmd.run:
#    - name: hostnamectl set-hostname {{ pillar['cluster'][grains['id']]['hostname'] }}

hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1     localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1           localhost localhost.localdomain localhost6 localhost6.localdomain6
        #--------------------------------------------------------------------------------#
        {% for node in pillar['cluster']['node_list'] %}
        {{ salt['mine.get'](node, 'mgmt_ip')[node] }} {{ salt['mine.get'](node, 'hostname')[node] }}
        {{ salt['mine.get'](node, 'data_ip')[node] }} {{ salt['mine.get'](node, 'hostname')[node] }}-data
        {% endfor %}
    - user: root
    - group: root
