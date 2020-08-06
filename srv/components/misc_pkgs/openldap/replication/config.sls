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
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.start

{% if pillar['cluster']['type'] != "single" -%}

Load provider module:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['admin']['secret']) }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif && sleep 2
    - watch_in:
      - Restart slapd service

Push provider for data replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['admin']['secret']) }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif && sleep 2
    - watch_in:
      - Restart slapd service

Configure openldap replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/cortx/provisioner/generated_configs/ldap/replicate.ldif 
    - watch_in:
      - Restart slapd service
    - require:
      - Push provider for data replication

{% endif -%}

# Validate replication configs are set using command:
# ldapsearch -w <ldappasswd> -x -D cn=admin,cn=config -b cn=config "olcSyncrepl=*"|grep olcSyncrepl: {0}rid=001
