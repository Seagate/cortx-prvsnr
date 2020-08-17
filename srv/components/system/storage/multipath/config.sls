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
  - components.system.storage.multipath.install

Stop multipath service:
  service.dead:
    - name: multipathd.service
    - require:
      - Install multipath

Copy multipath config:
  file.managed:
    - name: /etc/multipath.conf
    - source: salt://components/system/storage/multipath/files/multipath.conf
    - force: True
    - makedirs: True
    - require:
      - Install multipath
      - Stop multipath service

# Flush multipath:
#   cmd.run:
#     - name: multipath -F

{% if not pillar['cluster'][grains['id']]['is_primary'] -%}
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if pillar['cluster'][node_id]['is_primary'] %}
# Execute only on Secondary node
Copy multipath bindings to non-primary:
  cmd.run:
    - name: scp {{ pillar['cluster'][node_id]['hostname'] }}:/etc/multipath/bindings /etc/multipath/bindings
{%- endif %}
{% endfor %}
{%- endif %}

Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

{% if pillar['cluster'][grains['id']]['is_primary'] %}
Update cluster.sls pillar:
  module.run:
    - cluster.storage_device_config: []
    - saltutil.refresh_pillar: []
    - require:
      - Start multipath service
{% else %}
Update cluster.sls pillar:
  test.show_notification:
    - text: Update pillar doesn't work on Secondary node.
{% endif %}

Restart service multipath:
  module.run:
    - service.restart:
      - multipathd
    - require:
      - Update cluster.sls pillar
# End Setup multipath
