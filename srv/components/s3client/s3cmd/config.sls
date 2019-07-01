Configure s3cmd:
  file.managed:
    - name: /root/.s3cfg
    - contents:
      - ca_certs_file = /etc/ssl/stx-s3-clients/s3/ca.crt

# Create directory for s3cmd ssl certs:
#   file.directory:
#     - name: /root/.s3cmd/ssl/
#     - makedirs: True
#     - clean: True
#     - force: True

# Copy certs:
#   file.copy:
#     - name: /root/.s3cmd/ssl/ca.crt
#     - source: /etc/ssl/stx-s3-clients/s3/ca.crt
#     - makedirs: True
#     - preserve: True
