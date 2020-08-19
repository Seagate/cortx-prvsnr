#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

#-------------------------
# Teardown S3backgroundelete
#-------------------------


{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Stage - Post Install S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:reset')
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
