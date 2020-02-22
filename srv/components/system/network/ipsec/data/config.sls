Data interface config for IPSec channel:
  file.managed:
    - name: /etc/sysconfig/network-scripts/ifcfg-ipsec-data0
    - source: salt://components/system/network/ipsec/data/files/ifcfg-ipsec-data0
    - user: root
    - group: root
    - mode: 644
    - template: jinja

Data interface config for IPSec channel:
  file.managed:
    - name: /etc/sysconfig/network-scripts/keys-ipsec-data0
    - source: salt://components/system/network/ipsec/data/files/keys-ipsec-data0
    - user: root
    - group: root
    - mode: 600