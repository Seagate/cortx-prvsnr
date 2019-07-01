{% import_yaml 'components/defaults.yaml' as defaults %}

# Required for s3cmd installation
Add s3server_uploads yum repo:
  pkgrepo.managed:
    - name: {{ defaults.s3server.uploads_repo.id }}
    - enabled: True
    - humanname: s3server_uploads
    - baseurl: {{ defaults.s3server.uploads_repo.url }}
    - gpgcheck: 0
