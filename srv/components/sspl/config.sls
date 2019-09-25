# logrotate.d
Setup logrotate policy for rabbitmq-server:
  file.managed:
  - name: /etc/logrotate.d/rabbitmq-server
  - source: salt://components/sspl/files/etc/logrotate.d/rabbitmq-server
  - keep_source: False
  - user: root
  - group: root

{% set role = pillar['sspl']['role'] %}
# Copy conf file to /etc/sspl.conf
Copy sample file:
  file.copy:
    - name: /etc/sspl.conf
    - source: /opt/seagate/sspl/conf/sspl.conf.{{ pillar['sspl']['SYSTEM_INFORMATION']['product'] }}
    - mode: 644

Update SSPL config:
  module.run:
    - sspl.conf_update:
      - name: /etc/sspl.conf
      - ref_pillar: sspl
      - backup: True

Execute sspl_init script:
  cmd.run:
    - name: /opt/seagate/sspl/sspl_init config -f -r {{ role }}
    - onlyif: test -f /opt/seagate/sspl/sspl_init
