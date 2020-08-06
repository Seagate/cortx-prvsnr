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

{%- if pillar['cluster']['type'] != "single" -%}
{% for filename in [
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/create_replication_account.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/create_replication_account.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/check_ldap_replication.sh',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh' },
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
    - name: /opt/seagate/cortx/provisioner/generated_configs/ldap/hostlist.txt
    - contents: |
        {%- set node_list = (pillar['cluster']['node_list']) %}
        {{ grains['id'] -}}
        {%- for node in node_list | difference([grains['id']]) %}
        {{ node -}}
        {% endfor %}
    - user: root
    - group: root
    - require_in:
      - Replication sanity check

Replication sanity check:
  cmd.run:
    - name: sh /opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh -s /opt/seagate/cortx/provisioner/generated_configs/ldap/hostlist.txt -p {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['admin']['secret'],) }}
    - onlyif: test -f /opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh
{%- endif %}
