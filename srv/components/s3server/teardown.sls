#-------------------------
# Teardown haproxy/openldap
#-------------------------
include:
  - components.s3server.openldap.teardown
  - components.s3server.haproxy.teardown
  - components.s3server.keepalived.teardown
#-------------------------
# Teardown haproxy/openldap
#-------------------------

#-------------------------
# Teardown S3Server
#-------------------------
Remove S3Server:
  pkg.purged:
    - name: s3server

Remove s3server_uploads:
  pkg.purged:
    - pkgs:
      - python34-jmespath
      - python34-botocore
      - python34-s3transfer
      - python34-boto3
      - python34-xmltodict

Remove /tmp/s3certs:
  file.absent:
    - name: /tmp/s3certs

Remove working directory for S3 server:
  file.absent:
    - name: /var/seagate/s3

Remove S3Server under opt:
  file.absent:
    - name: /opt/seagate/s3server
#-------------------------
# Teardown S3Server End
#-------------------------

#-------------------------
# Teardown Common Runtime
#-------------------------
Disable http port in selinux:
  cmd.run:
    - name: setsebool httpd_can_network_connect false -P
    - onlyif: salt['grains.get']('selinux:enabled')

service_rsyslog:
  service.dead:
    - name: rsyslog
    - enable: False

remove_common_runtime:
  pkg.purged:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - libxml2
      - libyaml
      - yaml-cpp
      - gflags
      - glog
#------------------------------
# Teardown Common Runtime End
#------------------------------
