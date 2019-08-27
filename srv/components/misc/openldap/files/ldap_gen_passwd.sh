#!/bin/bash

ROOTDNPASSWORD="{{ salt['pillar.get']('openldap:admin_passwd', "seagate") }}"
LDAPADMINPASS="{{ salt['pillar.get']('openldap:iam_admin_passwd', "ldapadmin") }}"

SHA=$(slappasswd -s $ROOTDNPASSWORD)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/olcRootPW: *.*/olcRootPW: '$ESC_SHA'/g'
CFG_FILE=/opt/seagate/generated_configs/ldap/cfg_ldap.ldif
sed -i "$EXPR" $CFG_FILE

# generate encrypted password for ldap admin
SHA=$(slappasswd -s $LDAPADMINPASS)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/userPassword: *.*/userPassword: '$ESC_SHA'/g'
ADMIN_USERS_FILE=/opt/seagate/generated_configs/ldap/iam-admin.ldif
sed -i "$EXPR" $ADMIN_USERS_FILE