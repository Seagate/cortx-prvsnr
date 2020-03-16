Create Certs user:
  user.present:
    - name: certs

Create s3 certs directory:
  file.directory:
    - names:
      - /etc/ssl/stx-s3/s3
      - /etc/ssl/stx-s3/s3auth
    - makedirs: True
    - dir_mode: 755
    - file_mode: 644
    - user: certs
    - group: certs
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Certs user

