Setup Credentials:
  file.managed:
    - name: {{ salt['environ.get']('HOME') }}/.aws/credentials
    - source: salt://components/s3client/awscli/files/.aws/credentials
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
    - user: {{ salt['environ.get']('USER') }}
    - group: {{ salt['environ.get']('USER') }}
    - mode: 644

Setup Configurations:
  file.managed:
    - name: {{ salt['environ.get']('HOME') }}/.aws/config
    - source: salt://components/s3client/awscli/files/.aws/config
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
    - user: {{ salt['environ.get']('USER') }}
    - group: {{ salt['environ.get']('USER') }}
    - mode: 644
