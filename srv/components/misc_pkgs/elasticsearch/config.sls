Configure Elasticsearch:
  file.managed:
    - name: /etc/elasticsearch/elasticsearch.yml
    - source: salt://components/misc/elasticsearch/files/elasticsearch.yml
