#-------------------------
# Teardown haproxy/openldap
#-------------------------
# include:
#   - components.misc_pkgs.openldap.teardown
#   - components.ha.haproxy.teardown
#   - components.ha.keepalived.teardown
#-------------------------
# Teardown haproxy/openldap
#-------------------------

#-------------------------
# Teardown S3Server
#-------------------------
Stop s3authserver service:
  service.dead:
    - name: s3authserver
    - enable: False
    - init_delay: 2

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

Delete directory /opt/s3server/ssl:
  file.absent:
    - name: /opt/seagate/s3server/ssl

Delete directory /opt/s3server/s3certs:
  file.absent:
    - name: /opt/seagate/s3server/s3certs

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
Remove common_runtime libraries:
  pkg.purged:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - glog
      - gflags
      - yaml-cpp

#------------------------------
# Teardown Common Runtime End
#------------------------------

#------------------------------
# Teardown S3IAMCLI Start
#------------------------------
Remove S3 iamcli:
  pkg.removed:
    - pkgs:
      - s3iamcli
#       # - s3iamcli-devel
#       # - s3server-debuginfo
#------------------------------
# Teardown S3IAMCLI End
#------------------------------

{% import_yaml 'components/defaults.yaml' as defaults %}

Remove s3server_uploads repo:
  pkgrepo.absent:
    - name: {{ defaults.s3server.uploads_repo.id }}

Remove s3server repo:
  pkgrepo.absent:
    - name: {{ defaults.s3server.repo.id }}

Remove s3 entries from /etc/hosts:
 file.line:
   - name: /etc/hosts
   - match: '.*s3.seagate.com sts.seagate.com iam.seagate.com.*'
   - mode: delete

Delete s3server checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.s3server

