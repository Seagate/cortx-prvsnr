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

Remove s3 cert rpm:
  file.absent:
    - name: /opt/stx-s3-certs-1.0-1_s3dev.x86_64.rpm

remove s3client cert rpm:
  file.absent:
    - name: /opt/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

Remove working directory for S3 server:
  file.absent:
    - name: /var/seagate/s3

Remove S3Server under opt:
  file.absent:
    - name: /opt/seagate/s3server

Remove s3openldap cert:
  cmd.run:
    - name: keytool -delete -noprompt -alias ldapcert -trustcacerts -keystore /etc/ssl/stx-s3/s3auth/s3authserver.jks -storepass seagate
    - onlyif: test -f /etc/ssl/stx-s3/s3auth/s3authserver.jks

Remove s3server cert:
  cmd.run:
    - name: keytool -delete -noprompt -alias s3 -trustcacerts -keystore /etc/ssl/stx-s3/s3auth/s3authserver.jks -storepass seagate
    - onlyif: test -f /etc/ssl/stx-s3/s3auth/s3authserver.jks
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
