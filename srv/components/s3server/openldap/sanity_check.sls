Sanity check:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w seagate -D "cn=admin,dc=seagate,dc=com"
