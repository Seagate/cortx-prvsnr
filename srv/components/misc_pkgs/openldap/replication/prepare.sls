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
{% for filename in [
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/config.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/config.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/data.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/data.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/olcserverid.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/olcserverid.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/syncprov_config.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/syncprov_config.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/syncprov.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/syncprov.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/syncprov_mod.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/syncprov_mod.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/replicate.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/replicate.ldif'}

  ]
%}
{{ filename.dest }}:
  file.managed:
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
    - template: jinja
{% endfor %}
{%- endif %}
