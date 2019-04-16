{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_sources_dir = defaults.tmp_dir + "/s3certs/rpmbuild/SOURCES/" %}

#-------------------------
# Teardown openldap
#-------------------------
include:
  - components.s3server.openldap.teardown
#-------------------------
# Teardown openldap
#-------------------------

#-------------------------
# Teardown S3Server
#-------------------------

#-------------------------
# Teardown S3Server End
#-------------------------

#-------------------------
# Teardown Common Runtime
#-------------------------
service_rsyslog:
  service.dead:
    - name: rsyslog
    - enable: False

Remove keepalived master config:
  file.managed:
    - name: /etc/keepalived/keepalived.conf.master

Remove haproxy config to enable logs:
  file.absent:
    - name: /etc/rsyslog.d/haproxy.conf

Remove haproxy 503 error code to http file:
  file.absent:
    - name: /etc/haproxy/errors/503.http

Remove /tmp/s3certs:
  file.absent:
    - name: /tmp/s3certs

Remove working directory for S3 server:
  file.absent:
    - name: /var/seagate/s3

remove_common_runtime:
  pkg.purged:
    - pkgs:
      - keepalived
      - haproxy
      - glog
      - gflags
      - yaml-cpp
      - openssl
      - openssl-libs
      - libxml2
      - libyaml
      - java-1.8.0-openjdk-headless
#------------------------------
# Teardown Common Runtime End
#------------------------------
