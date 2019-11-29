Remove awscli-plugin-endpoint:
  pip.removed:
    - name: awscli-plugin-endpoint
    - bin_env: '/usr/bin/pip3'

Remove AWS CLI:
  pip.removed:
    - name: awscli
    - bin_env: '/usr/bin/pip3'

Ensure AWS credentials file is removed:
  file.absent:
    - name: /root/.aws/credentials

Ensure AWS config file is removed:
  file.absent:
    - name: /root/.aws/config
