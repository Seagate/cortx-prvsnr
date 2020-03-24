Remove certs directory:
  file.absent:
    - names:
      - /etc/ssl/stx

Remove certs group:
  group.absent:
    - name: certs
