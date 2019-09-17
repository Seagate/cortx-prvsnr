service_dcs_collector:
  cmd.run:
    - name: /etc/rc.d/init.d/dcs-collector stop
    - onlyif: test -f /etc/rc.d/init.d/dcs-collector

stop service sspl-ll:
  service.dead:
    - name: sspl-ll

Stop rabbitmq-server:
  service.dead:
    - name: rabbitmq-server

