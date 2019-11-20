Start rabbitmq-server:
  service.running:
    - name: rabbitmq-server

start service sspl-ll:
  service.running:
    - name: sspl-ll
