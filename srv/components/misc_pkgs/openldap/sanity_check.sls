Verify ldap certificates valid and slapd is running:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w {{ pillar['openldap']['admin']['secret'] }} -D "cn=admin,dc=seagate,dc=com" -H ldap://
