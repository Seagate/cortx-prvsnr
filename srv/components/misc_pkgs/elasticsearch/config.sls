Configure Elasticsearch:
  file.managed:
    - name: /etc/elasticsearch/elasticsearch.yml
    - source: salt://components/misc_pkgs/elasticsearch/files/elasticsearch.yml.j2
    - template: jinja

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Create elastic_search index:
  module.run:
    - name: http.query
    - url: http://{{ grains["host"] }}:{{ pillar["elasticsearch"]["http_port"] }}/myindex/user/dilbert
    - method: PUT
    - header: "Content-Type: application/json"
    - data: '{"name":"Myname"}'
    - raise_error: True

Set data auto-replication:
  module.run:
    - name: http.query
    - url: {{ grains["host"] }}:{{ pillar["elasticsearch"]["http_port"] }}/myindex/_settings
    - method: PUT
    - header: "Content-Type: application/json"
    - data: '{"index":{"number_of_replicas":"2","auto_expand_replicas":"2-all"}}'
    - raise_error: True
{% endif %}
