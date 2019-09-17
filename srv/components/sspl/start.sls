Start rabbitmq-server:
  service.running:
    - name: rabbitmq-server

Start service dcs-collector:
  cmd.run:
    - name: /etc/rc.d/init.d/dcs-collector start
    - onlyif: test -f /etc/rc.d/init.d/dcs-collector

start service sspl-ll:
  service.running:
    - name: sspl-ll
