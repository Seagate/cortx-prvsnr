Remove elasticsearch:
  pkg.purged:
    - name: elasticsearch


Remove elasticsearch config:
  file.absent:
    - name: /etc/elasticsearch/elasticsearch.yml
