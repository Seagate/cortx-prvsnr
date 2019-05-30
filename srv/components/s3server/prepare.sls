{% import_yaml 'components/defaults.yaml' as defaults %}

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

Update to latest selinux-policy (required by latest openldap):
  pkg.installed:
    - name: selinux-policy

Enable http port in selinux:
  cmd.run:
    - name: setsebool httpd_can_network_connect true -P
    - onlyif: salt['grains.get']('selinux:enabled')

Create working directory for S3 server:
  file.directory:
    - name: /var/seagate/s3
    - makedirs: True
