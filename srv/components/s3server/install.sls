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
    - name: cortx-s3server
    - version: {{ pillar['s3server']['version']['cortx-s3server'] }}
    - refresh: True

Install cortx-s3iamcli:
  pkg.installed:
    - pkgs:
      - cortx-s3iamcli: {{ pillar['s3server']['version']['cortx-s3iamcli'] }}
      # - s3iamcli-devel
      # - s3server-debuginfo
