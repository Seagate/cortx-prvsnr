Create certs group:
  group.present:
    - name: certs
    - addusers: root

Create s3 certs directory:
  file.directory:
    - names:
      - /etc/ssl/stx
    - makedirs: True
    - dir_mode: 750
    - file_mode: 640
    - user: root
    - group: certs
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Certs user

