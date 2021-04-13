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
{% set server_nodes = [ ] %}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}

include:
  - components.ha.corosync-pacemaker.config.base

Authorize nodes:
  pcs.auth:
    - name: pcs_auth__auth
    - nodes:
      {%- for node_id in server_nodes %}
      - {{ node_id }}
      {%- endfor %}
    - pcsuser: {{ pillar['cortx']['software']['corosync-pacemaker']['user'] }}
    - pcspasswd: {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['corosync-pacemaker']['secret']) }}
    - extra_args:
      - '--force'
    - require:
      - Start pcsd service
