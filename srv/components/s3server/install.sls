install_common_runtime:
  pkg.installed:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - libxml2
      - libyaml
      - yaml-cpp
      - gflags
      - glog

install_s3server_uploads:
  pkg.installed:
    - pkgs:
      - python34-jmespath
      - python34-botocore
      - python34-s3transfer
      - python34-boto3
      - python34-xmltodict

# Only for client
# install_s3s3iamcli:
#   pkg.installed:
#     - pkgs:
#       - s3iamcli
#       # is this required in PROD?
#       # - s3iamcli-devel
#       # - s3server-debuginfo

install_s3server:
  pkg.installed:
    - name: s3server
