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
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/config.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/config.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/data.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/data.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/olcserverid.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/olcserverid.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/syncprov_config.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_config.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/syncprov.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/syncprov_mod.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/replication/files/replicate.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/replicate.ldif'}

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
