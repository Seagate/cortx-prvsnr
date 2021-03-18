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
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.start
  - components.misc_pkgs.openldap.sanity_check

{% set server_nodes = [ ] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
{% if 1 < (server_nodes|length) -%}
{% set ldap_password = salt['lyveutil.decrypt']('openldap', pillar['cortx']['software']['openldap']['root']['secret']) -%}

Load provider module:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/syncprov_mod.ldif && sleep 2
    - env:
      - password: {{ ldap_password }}
    - watch_in:
      - Restart slapd service

Push provider for data replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/syncprov.ldif && sleep 2
    - env:
      - password: {{ ldap_password }}
    - watch_in:
      - Restart slapd service

Configure openldap replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/cortx_configs/provisioner_generated/ldap/replicate.ldif && sleep 10 
    - watch_in:
      - Restart slapd service
    - require:
      - Push provider for data replication
    - onchanges:
      - Verify ldap certificates valid and slapd is running

Cleanup ldif files:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/ldap

{% endif -%}
