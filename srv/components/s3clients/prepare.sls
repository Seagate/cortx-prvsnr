{% import_yaml 'components/defaults.yaml' as defaults %}

# Copy certs from s3server:
#   cmd.run:
#     - name: scp {{ pillar['s3clients']['s3server']['ip'] }}:/opt/seagate/stx-s3-client-certs-*.rpm /opt/seagate
#     - unless: test -f /opt/seagate/stx-s3-client-certs-*

Copy client certs:
  file.managed:
    - name: /etc/ssl/stx-s3-clients/s3/ca.crt
    - source: salt://components/s3clients/files/ca.crt
    - makedirs: True
    - force: True
    - mode: 444

Add s3server_uploads yum repo:
  pkgrepo.managed:
    - name: {{ defaults.s3server.uploads_repo.id }}
    - enabled: True
    - humanname: s3server_uploads
    - baseurl: {{ defaults.s3server.uploads_repo.url }}
    - gpgcheck: 0

Add s3server yum repo:
  pkgrepo.managed:
    - name: {{ defaults.s3server.repo.id }}
    - enabled: True
    - baseurl: {{ defaults.s3server.repo.url }}
    - gpgcheck: 0
