Set hostname:
  cmd.run:
    - name: hostnamectl set-hostname {{ pillar['cluster'][grains['id']]['hostname'] }}

hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
    - user: root
    - group: root
