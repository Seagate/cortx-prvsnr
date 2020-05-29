include:
  - components.misc_pkgs.elasticsearch.install
  - components.misc_pkgs.rsyslog

Configure Elasticsearch:
  file.managed:
    - name: /etc/elasticsearch/elasticsearch.yml
    - source: salt://components/misc_pkgs/elasticsearch/files/elasticsearch.yml.j2
    - template: jinja

{% if salt["grains.get"]('is_primary', false) %}
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

Load rsyslog module for elasticsearch:
  file.line:
    - name: /etc/rsyslog.conf
    - after: "#### MODULES ####"
    - content: |
        # load omelasticsearch to redirect logs to elasticsearch
        module(load="omelasticsearch")
    - mode: ensure
    - require:
      - Install rsyslog extras
    - watch_in:
      - service: Start rsyslog
