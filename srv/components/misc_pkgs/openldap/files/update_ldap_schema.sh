#!/bin/bash -e
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

# Script to update schema and initialize ldap for S3 Authserver.
# CAUTION: This scipt will delete existing S3 user data.

USAGE="USAGE: bash $(basename "$0") [--defaultpasswd] [-h | --help]
Update S3 schema in OpenLDAP.

where:
--defaultpasswd     use default password i.e. 'seagate' for LDAP
--help              display this help and exit"

defaultpasswd=false
case "$1" in
    --defaultpasswd )
        defaultpasswd=true
        ;;
    --help | -h )
        echo "$USAGE"
        exit 1
        ;;
esac

PASSWORD="seagate"
if [[ $defaultpasswd == false ]]
then
    echo -n "Enter Password for LDAP: "
    read -s PASSWORD && [[ -z $PASSWORD ]] && echo 'Password can not be null.' && exit 1
fi

# Delete all the entries from LDAP.
ldapdelete -x -w $PASSWORD -D "cn=admin,dc=seagate,dc=com" -r "dc=seagate,dc=com"

# Stop slapd
systemctl stop slapd

# Delete the schema from LDAP.
rm -f /etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif

# Start slapd
systemctl start slapd

# Add S3 schema
ldapadd -x -w $PASSWORD -D "cn=admin,cn=config" -f cn\=\{1\}s3user.ldif

# Restart slapd to update the changes
systemctl restart slapd

# Initialize ldap
ldapadd -x -w $PASSWORD -D "cn=admin,dc=seagate,dc=com" -f ldap-init.ldif
