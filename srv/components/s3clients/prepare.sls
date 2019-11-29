{% import_yaml 'components/defaults.yaml' as defaults %}

Copy certs from s3server:
  cmd.run:
    - name: scp {{ pillar['s3client']['s3server']['hostname'] }}:/opt/seagate/stx-s3-client-certs-*.rpm /opt/seagate
    - unless: test -f /opt/seagate/stx-s3-client-certs-*

Install certs:
  pkg.installed:
    - sources:
      - stx-s3-client-certs: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

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
