Copy certs to destination:
  file.managed:
    - name: /etc/ssl/stx/stx.pem
    - source:
      - salt://components/misc_pkgs/ssl_certs/files/stx.pem
      - salt://components/misc_pkgs/ssl_certs/files/s3server.pem
    - makedirs: True
