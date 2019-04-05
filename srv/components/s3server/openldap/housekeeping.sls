delete_dir_tmp_slapd:
  file.absent:
    - name: /tmp/s3ldap
