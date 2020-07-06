{%- set db = pillar['openldap']['backend_db'] -%}
#!/bin/bash

{%- set openldap_admin_secret = salt['lyveutil.decrypt'](salt['pillar.get']('openldap:admin:secret', "seagate"), 'openldap') %}
{%- set openldap_iam_secret = salt['lyveutil.decrypt'](salt['pillar.get']('openldap:iam_admin:secret', "ldapadmin"), 'openldap') %}

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
