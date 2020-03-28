#!/bin/bash

{% set openldap_admin_secret = salt['lyveutil.decrypt'](salt['pillar.get']('openldap:admin:secret', "seagate"), 'openldap') %}
{% set openldap_iam_secret = salt['lyveutil.decrypt'](salt['pillar.get']('openldap:iam_admin:secret', "ldapadmin"), 'openldap') %}

ROOTDNPASSWORD="{{ openldap_admin_secret }}"
LDAPADMINPASS="{{ openldap_iam_secret }}"

SHA=$(slappasswd -s $ROOTDNPASSWORD)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/olcRootPW: *.*/olcRootPW: '$ESC_SHA'/g'
CFG_FILE=/opt/seagate/eos-prvsnr/generated_configs/ldap/cfg_ldap.ldif
sed -i "$EXPR" $CFG_FILE

{%- set db = pillar['openldap']['backend_db'] -%}
{% if 'mdb' in db -%}
# CFG_FILE=/opt/seagate/eos-prvsnr/generated_configs/ldap/olcDatabase={2}{{db}}.ldif
# sed -i "$EXPR" $CFG_FILE
{%- endif %}

# generate encrypted password for ldap admin
SHA=$(slappasswd -s $LDAPADMINPASS)
ESC_SHA=$(echo $SHA | sed 's/[/]/\\\//g')
EXPR='s/userPassword: *.*/userPassword: '$ESC_SHA'/g'
ADMIN_USERS_FILE=/opt/seagate/eos-prvsnr/generated_configs/ldap/iam-admin.ldif
sed -i "$EXPR" $ADMIN_USERS_FILE
