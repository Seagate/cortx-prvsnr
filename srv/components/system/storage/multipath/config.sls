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
  - components.system.storage.multipath.stop

Copy multipath config:
  file.managed:
    - name: /etc/multipath.conf
    - source: salt://components/system/storage/multipath/files/multipath.conf
    - force: True
    - makedirs: True
    - template: jinja
    - require:
      - Install multipath
      - Stop multipath service

# Flush multipath:
#   cmd.run:
#     - name: multipath -F


{% set enclosure_id = "enclosure-" + ((grains['id']).split('_'))[1] %}
{% if not 'JBOD' in pillar['storage'][enclosure_id]['controller']['type'] %}
{% if (not "primary" in pillar["cluster"][grains["id"]]["roles"])
    or (pillar['cluster']['replace_node']['minion_id']
    and grains['id'] == pillar['cluster']['replace_node']['minion_id'])
%}

{% set server_nodes = [ ] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
{% set node_id = (server_nodes | difference(grains['id']))[0] %}
# Execute only on Secondary node
Copy multipath bindings:
  cmd.run:
    - name: scp {{ node_id }}:/etc/multipath/bindings /etc/multipath/bindings
{% endif %} # Check if primary node or replacement node end

Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

{% if "primary" in pillar["cluster"][grains["id"]]["roles"]
    and not (pillar['cluster']['replace_node']['minion_id']
    and grains['id'] == pillar['cluster']['replace_node']['minion_id'])
%}
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
{% endif %} # Check for mpath device list generation end

{% else -%}
# Changes specific to JBOD
Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

Check multipath devices:
  cmd.run:
    - name: test `multipath -ll | grep mpath | wc -l` -ge 7
    - retry:
        attempts: 3
        until: True
        interval: 5

Update cluster.sls pillar:
  module.run:
    - cluster.jbod_storage_config: []
    - saltutil.refresh_pillar: []
    - require:
      - Start multipath service
      - Check multipath devices
{% endif %} # end of JBOD check

Restart service multipath:
  module.run:
    - service.restart:
      - multipathd
    - require:
      - Update cluster.sls pillar
# End Setup multipath
