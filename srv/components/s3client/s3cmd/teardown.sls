Remove s3cmd package:
  pkg.removed:
    - name: s3cmd

Ensure s3cmd config file is removed:
  file.absent:
    - name: /root/.s3cfg

Ensure the cert directory is removed:
  file.absent:
    - name: /root/.s3cmd/ssl
