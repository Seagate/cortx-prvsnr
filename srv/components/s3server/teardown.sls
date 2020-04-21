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

Remove eos-s3server:
  pkg.purged:
    - name: eos-s3server

#Remove s3server_uploads:
#  pkg.purged:
#    - pkgs:
#      - python34-jmespath
#      - python34-botocore
#      - python34-s3transfer
#      - python34-boto3
#      - python34-xmltodict

#Remove /tmp/s3certs:
#  file.absent:
#    - name: /tmp/s3certs

#Delete directory /opt/s3server/ssl:
#  file.absent:
#    - name: /opt/seagate/s3server/ssl

#Delete directory /opt/s3server/s3certs:
#  file.absent:
#    - name: /opt/seagate/s3server/s3certs

#Remove working directory for S3 server:
#  file.absent:
#    - name: /var/seagate/s3

Remove S3Server under opt:
  file.absent:
    - name: /opt/seagate/s3server

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
Remove eos-s3iamcli:
  pkg.removed:
    - pkgs:
      - eos-s3iamcli
#       # - eos-s3iamcli
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

