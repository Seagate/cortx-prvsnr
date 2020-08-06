#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

include:
  - components.misc_pkgs.elasticsearch.install
  - components.misc_pkgs.rsyslog

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
