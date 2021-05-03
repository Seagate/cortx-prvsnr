#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
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

{% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}
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

Delete elasticsearch security plugin:
  file.absent:
    - name: /usr/share/elasticsearch/plugins/opendistro_security

Reload service units:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: Configure Elasticsearch
