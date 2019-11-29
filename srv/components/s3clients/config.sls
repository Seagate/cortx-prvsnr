Generate base credentials:
  cmd.run:
    - name: /bin/s3iamcli createaccount -n s3user -e s3user@seagate.com --ldapuser sgiamadmin --ldappasswd ldapadmin  | tee /opt/seagate/.s3-client-credentials
    - only_if: test -f /bin/s3iamcli
