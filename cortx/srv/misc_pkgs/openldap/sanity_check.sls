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

Verify ldap certificates valid and slapd is running:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w $password -D "cn=admin,dc=seagate,dc=com" -H ldap://
    - env:
      - password: {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }}
