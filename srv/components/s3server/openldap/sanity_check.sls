sanity_check:
  cmd.run:
    - name: ldapsearch -b "dc=s3,dc=seagate,dc=com" -x -w seagate -D "cnd=admin,dc=seagate,dc=com"
