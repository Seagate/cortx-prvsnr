{% import_yaml 'components/defaults.yaml' as defaults %}
Remove RabbitMQ packages:
  pkg.purged:
    - name: rabbitmq-server
