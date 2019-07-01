Ensure driver config is removed:
  file.absent:
    - name: /opt/cos/conf/driver.conf

Ensure controller config is removed:
  file.absent:
    - name: /opt/cos/conf/controller.conf

Ensure cosbench directory is removed:
  file.absent:
    - name: /opt/cos

Close driver port:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: DROP
    - protocol: tcp
    - match: tcp
    - dport: 18088
    - connstate: NEW
    - family: ipv4
    - save: True

Close controller port:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: DROP
    - protocol: tcp
    - match: tcp
    - dport: 19088
    - family: ipv4
    - save: True
