Install common runtime libraries:
  pkg.installed:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - libxml2
      - libyaml
      - yaml-cpp
      - gflags
      - glog

# Install from s3server_uploads packages:
#   pkg.installed:
#     - pkgs:
#       - python34-boto3
#       - python34-botocore
#       - python34-jmespath
#       - python34-s3transfer
#       - python34-xmltodict

Install s3server package:
  pkg.installed:
    - name: eos-s3server
    - version: {{ pillar['s3server']['version']['eos-s3server'] }}
    - refresh: True

Install eos-s3iamcli:
  pkg.installed:
    - pkgs:
      - eos-s3iamcli: {{ pillar['s3server']['version']['eos-s3iamcli'] }}
      # - s3iamcli-devel
      # - s3server-debuginfo
