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

#!/bin/bash

{%- set openldap_admin_secret = salt['lyveutil.decrypt']('openldap', salt['pillar.get']('openldap:admin:secret', "seagate")) %}
{%- set openldap_iam_secret = salt['lyveutil.decrypt']('openldap', salt['pillar.get']('openldap:iam_admin:secret', "ldapadmin")) %}

ROOTDNPASSWORD="{{ openldap_admin_secret }}"
LDAPADMINPASS="{{ openldap_iam_secret }}"

SHA=$(slappasswd -s $ROOTDNPASSWORD)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/olcRootPW: *.*/olcRootPW: '$ESC_SHA'/g'
CFG_FILE=/opt/seagate/cortx/provisioner/generated_configs/ldap/cfg_ldap.ldif
sed -i "$EXPR" $CFG_FILE

# generate encrypted password for ldap admin
SHA=$(slappasswd -s $LDAPADMINPASS)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/userPassword: *.*/userPassword: '$ESC_SHA'/g'
ADMIN_USERS_FILE=/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin.ldif
sed -i "$EXPR" $ADMIN_USERS_FILE
