#-------------------------
# Teardown S3backgroundelete
#-------------------------


{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Stage - Post Install S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/s3server/conf/setup.yaml', 's3server:reset')
{% endif %}


#-------------------------
# Teardown S3Server
#-------------------------
Stop s3authserver service:
  service.dead:
    - name: s3authserver
    - enable: False
    - init_delay: 2

Remove cortx-s3server:
  pkg.purged:
    - name: cortx-s3server

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
Remove cortx-s3iamcli:
  pkg.removed:
    - pkgs:
      - cortx-s3iamcli
#       # - cortx-s3iamcli
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

Delete s3server checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.s3server
