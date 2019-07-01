Configure s3cmd:
  file.managed:
    - name: {{ salt['environ.get']('HOME') }}/.s3cfg
    - source: salt://components/s3client/s3cmd/files/.s3cfg
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
    - user: {{ salt['environ.get']('USER') }}
    - group: {{ salt['environ.get']('USER') }}
    - mode: 644

Create directory for s3cmd ssl certs:
  file.directory:
    - name: {{ salt['environ.get']('HOME') }}/.s3cmd/ssl
    - makedirs: True
    - clean: True
    - force: True

Copy certs:
  file.copy:
    - name: {{ salt['environ.get']('HOME') }}/.s3cmd/ssl/ca.crt
    - source: /etc/ssl/stx-s3-clients/s3/ca.crt
    - makedirs: True
    - preserve: True
