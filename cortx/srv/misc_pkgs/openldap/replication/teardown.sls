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

{% set server_nodes = [ ] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
{% if 1 < (server_nodes|length) -%}
# Cleanup
{% for filename in [
    '/opt/seagate/cortx_configs/provisioner_generated/ldap/create_replication_account.ldif',
    '/opt/seagate/cortx_configs/provisioner_generated/ldap/check_ldap_replication.sh',
    '/opt/seagate/cortx_configs/provisioner_generated/ldap/replicate.ldif',
    '/opt/seagate/cortx_configs/provisioner_generated/ldap/hostlist.txt'
  ]
%}
{{ filename }}_del:
  file.absent:
    - name: {{ filename }}
{% endfor %}

Delete openldap replication checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.openldap_replication

{%- endif %}
