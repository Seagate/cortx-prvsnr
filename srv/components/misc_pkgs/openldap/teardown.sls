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
  - components.misc_pkgs.openldap.replication.teardown

# Kind of slapd cleanup from here
Stop slapd:
  service.dead:
    - name: slapd

disable slapd:
  service.disabled:
    - name: slapd

Remove pkgs:
  pkg.purged:
    - pkgs:
      - openldap-servers
      - openldap-clients
    - require:
      - Stop slapd

# File cleanup operation
{% for filename in [
   '/etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif',
   '/var/lib/ldap',
   '/etc/sysconfig/slapd',
   '/etc/sysconfig/slapd.bak',
   '/etc/openldap/slapd.d',
   '/opt/seagate/cortx_configs/provisioner_generated/ldap'
 ] %}
{{ filename }}:
  file.absent:
    - require:
      - pkg: Remove pkgs
{% endfor %}

Remove user ldap:
  user.absent:
    - name: ldap
    - purge: True
    - force: True

# Attention: Do not delete the /etc/openldap/certs dir at any cost
# Remove ldap configurations:
#   file.absent:
#     - name: /etc/openldap

Reset permissions:
  file.directory:
    - name: /etc/openldap/certs
    - user: root
    - group: root
    - recurse:
      - user
      - group

Delete openldap checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.openldap
