Remove packages:
  pkg.purged:
    - pkgs:
      - sspl-test
      - sg3_utils
      - openhpi
      - gemhpi
      - pull_sea_logs
      - python-daemon
      - python-hpi
      - python-openhpi-baselib
      - zabbix-agent-lib
      - zabbix-api-gescheit
      - zabbix-xrtx-lib
      - zabbix-collector
      - lxqt-policykit

Remove sspl packages:
  pkg.purged:
    - pkgs:
      - lxqt-policykit
      - libsspl_sec
      - libsspl_sec-method_none
      - sspl

Remove file sspl_ll.conf:
  file.absent:
    - name: /etc/sspl_ll.conf

Remove file dcs_collector.conf:
  file.absent:
    - name: /etc/dcs_collector.conf

Remove directory dcs_collector.conf.d:
  file.absent:
    - name: /etc/dcs_collector.conf.d

Remove directory install sspl:
  file.absent:
    - name: /opt/seagate/sspl

Remove test fw lettuce:
  pip.removed:
    - name: lettuce

Remove user sspl-ll:
  user.absent:
    - name: sspl-ll
    - purge: True
    - force: True

Remove user zabbix:
  user.absent:
    - name: zabbix
    - purge: True
    - force: True

Remove user rabbitmq:
  user.absent:
    - name: rabbitmq
    - purge: True
    - force: True
