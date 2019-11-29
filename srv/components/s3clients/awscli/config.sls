Setup Credentials:
  file.managed:
    - name: ~/.aws/credentials
    - source: salt://components/s3client/awscli/files/.aws/credentials
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
    - user: {{ salt['grains.get']('username') }}
    - group: {{ salt['grains.get']('groupname') }}
    - mode: 644

Setup Configurations:
  file.managed:
    - name: ~/.aws/config
    - source: salt://components/s3client/awscli/files/.aws/config
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
    - user: {{ salt['grains.get']('username') }}
    - group: {{ salt['grains.get']('groupname') }}
    - mode: 644
