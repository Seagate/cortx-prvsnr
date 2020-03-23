Remove certs directory:
  file.absent:
    - names:
      - /etc/ssl/stx

Remove certs user:
  user.absent:
    - name: certs

Remove certs group:
  group.absent:
    - name: certs
