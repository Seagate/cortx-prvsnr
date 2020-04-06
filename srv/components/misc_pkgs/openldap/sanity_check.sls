Verify ldap certificates valid and slapd is running:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap://
