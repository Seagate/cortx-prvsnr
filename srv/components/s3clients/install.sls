Install requisites:
  pkg.installed:
    - pkgs:
      - python34-boto3
      - python34-botocore
      - python34-jmespath
      - python34-s3transfer
      - python34-xmltodict

Install s3iamcli:
  pkg.installed:
    - pkgs:
      - s3iamcli
#       # - s3iamcli-devel
#       # - s3server-debuginfo
