Install common runtime libraries:
  pkg.installed:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - libxml2
      - libyaml
      - yaml-cpp
      - gflags
      - glog

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
