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
# please email opensource@seagate.com or cortx-questions@seagate.com."
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

{% if 'JBOD' not in pillar["storage_enclosure"]["controller"]["type"] -%}
{% if not pillar['cluster'][grains['id']]['is_primary'] -%}
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if pillar['cluster'][node_id]['is_primary'] %}
# Execute only on Secondary node
Copy multipath bindings to non-primary:
  cmd.run:
    - name: scp {{ node_id }}:/etc/multipath/bindings /etc/multipath/bindings
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

{% else -%}
Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

Update cluster.sls pillar:
  module.run:
    - cluster.jbod_storage_config: []
    - saltutil.refresh_pillar: []
    - require:
      - Start multipath service
{% endif %}

Restart service multipath:
  module.run:
    - service.restart:
      - multipathd
    - require:
      - Update cluster.sls pillar
# End Setup multipath
