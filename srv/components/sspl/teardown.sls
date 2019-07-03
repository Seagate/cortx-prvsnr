service_dcs_collector:
  cmd.run:
    - name: /etc/rc.d/init.d/dcs-collector stop
    - onlyif: test -f /etc/rc.d/init.d/dcs-collector

{% if 'virtual' in salt['grains.get']('productname').lower() %}

Remove packages:
  pkg.purged:
    - pkgs:
      - lxqt-policykit

{% else %}

Remove packages:
  pkg.purged:
    - pkgs:
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

{% endif %}

stop service sspl-ll:
  service.dead:
    - name: sspl-ll

stop service rabbitmq-server:
  service.dead:
    - name: rabbitmq-server

Remove sspl packages:
  pkg.purged:
    - pkgs:
      - sspl
      - libsspl_sec-method_none
      - libsspl_sec
      - rabbitmq-server

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

# Remove test fw lettuce:
#   pip.removed:
#     - name: lettuce
#     - bin_env: '/usr/bin/pip3'
