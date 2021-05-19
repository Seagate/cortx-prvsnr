#!/bin/bash
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


{%- set openldap_admin_secret = salt['lyveutils.decrypt']('cortx', salt['pillar.get']('cortx:software:openldap:root:secret', "seagate")) %}
{%- set openldap_iam_secret = salt['lyveutils.decrypt']('cortx', salt['pillar.get']('cortx:software:openldap:sgiam:secret', "ldapadmin")) %}

ROOTDNPASSWORD="{{ openldap_admin_secret }}"
LDAPADMINPASS="{{ openldap_iam_secret }}"

SHA=$(slappasswd -s $ROOTDNPASSWORD)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/olcRootPW: *.*/olcRootPW: '$ESC_SHA'/g'
CFG_FILE=/opt/seagate/cortx_configs/provisioner_generated/ldap/cfg_ldap.ldif
sed -i "$EXPR" $CFG_FILE

# generate encrypted password for ldap admin
#SHA=$(slappasswd -s $LDAPADMINPASS)
#ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/userPassword: *.*/userPassword: '$LDAPADMINPASS'/g'
ADMIN_USERS_FILE=/opt/seagate/cortx_configs/provisioner_generated/ldap/iam-admin.ldif
sed -i "$EXPR" $ADMIN_USERS_FILE
