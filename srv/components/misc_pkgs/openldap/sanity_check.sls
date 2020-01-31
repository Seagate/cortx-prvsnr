Verify ldap certificates valid and slapd is running:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w {{ pillar['openldap']['admin_passwd'] }} -D "cn=admin,dc=seagate,dc=com" -H ldap://

Verify ldaps certificates valid and slapd is running:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w {{ pillar['openldap']['admin_passwd'] }} -D "cn=admin,dc=seagate,dc=com" -H ldaps://
