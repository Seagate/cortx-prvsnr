Configure Elasticsearch:
  file.managed:
    - name: /etc/elasticsearch/elasticsearch.yml
    - source: salt://components/misc_pkgs/elasticsearch/files/elasticsearch.yml
