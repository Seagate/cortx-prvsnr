Setup Credentials:
  file.managed:
    - name: /root/.aws/credentials
    - source: salt://components/s3client/awscli/files/.aws/credentials
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True

Setup Configurations:
  file.managed:
    - name: /root/.aws/config
    - source: salt://components/s3client/awscli/files/.aws/config
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
