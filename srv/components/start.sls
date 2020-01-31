Start rabbitmq-server:
  service.running:
    - name: rabbitmq-server

include:
  - components.sspl.start
  - components.eoscore.start
  - components.ha.haproxy.start
  - components.s3server.start
  - components.hare.start
  - components.ha.haproxy.start


