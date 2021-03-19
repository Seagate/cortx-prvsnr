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
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/create_replication_account.ldif',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/create_replication_account.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/check_ldap_replication.sh',
      "dest": '/opt/seagate/cortx_configs/provisioner_generated/ldap/check_ldap_replication.sh' },
  ]
%}
{{ filename.dest }}_copy:
  file.managed:
    - name: {{ filename.dest }}
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
    - template: jinja
    - require_in:
      - Replication sanity check
{% endfor %}

Hostlist file:
  file.managed:
    - name: /opt/seagate/cortx_configs/provisioner_generated/ldap/hostlist.txt
    - contents: |
        {{ grains['id'] -}}
        {%- for node in (server_nodes | difference([grains['id']])) %}
        {{ node -}}
        {% endfor %}
    - user: root
    - group: root
    - require_in:
      - Replication sanity check

Replication sanity check:
  cmd.run:
    - name: sh /opt/seagate/cortx_configs/provisioner_generated/ldap/check_ldap_replication.sh -s /opt/seagate/cortx_configs/provisioner_generated/ldap/hostlist.txt -p $password || true
    - env:
      - password: {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['root']['secret']) }}
    - onlyif: test -f /opt/seagate/cortx_configs/provisioner_generated/ldap/check_ldap_replication.sh
    - watch_in:
      - Restart slapd service

{%- endif %}
