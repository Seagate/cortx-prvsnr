Install requisites:
  pkg.installed:
    - pkgs:
      - python36-boto3
      - python36-botocore
      - python36-jmespath
      - python36-s3transfer
      - python36-xmltodict

# Install certs:
#   pkg.installed:
#     - sources:
#       - stx-s3-client-certs: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

Install eos-s3iamcli:
  pkg.installed:
    - pkgs:
      - eos-s3iamcli: latest
#       # - eos-s3iamcli-devel
