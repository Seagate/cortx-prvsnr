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

Create tmp dir:
  file.directory:
    - name: /opt/seagate/cortx/provisioner/generated_configs/ldap
    - clean: True
    - makedirs: True
    - force: True

# File copy operation on primary
{% for filename in [
    { "src": 'salt://components/misc_pkgs/openldap/files/cfg_ldap.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/cfg_ldap.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/cn={1}s3user.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/cn={1}s3user.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/iam-admin-access.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin-access.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/iam-admin.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/iam-constraints.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-constraints.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/ldap_gen_passwd.sh',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ldap_gen_passwd.sh' },
    { "src": 'salt://components/misc_pkgs/openldap/files/ldap-init.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ldap-init.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/olcDatabase={2}mdb.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/olcDatabase={2}mdb.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/ppolicy-default.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicy-default.ldif'},
    { "src": 'salt://components/misc_pkgs/openldap/files/ppolicymodule.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicymodule.ldif'},
    { "src": 'salt://components/misc_pkgs/openldap/files/ppolicyoverlay.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicyoverlay.ldif'},
    { "src": 'salt://components/misc_pkgs/openldap/files/slapdlog.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/slapdlog.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/test_data.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/test_data.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/resultssizelimit.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/resultssizelimit.ldif' },
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
