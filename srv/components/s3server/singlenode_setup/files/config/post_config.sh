#!/bin/bash

script_dir=$(dirname $0)

set -e

/opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l ldapadmin -p /opt/seagate/auth/resources/authserver.properties
systemctl restart s3authserver
sleep 30

s3iamcli createaccount -n s3user -e s3user@seagate.com --ldapuser sgiamadmin --ldappasswd ldapadmin  | tee ~/s3-client-credentials

echo "EOS configuration completed. Run 'hctl mero status'" \
    "to check EOS status and ensure all services are oniline before using it."
