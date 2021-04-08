#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#


{% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}
Stage - Cleanup S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3:cleanup')
{% endif %}


# #-------------------------
# # Teardown S3Server
# #-------------------------
# Stop s3authserver service:
#   service.dead:
#     - name: s3authserver
#     - enable: False
#     - init_delay: 2

# Remove cortx-s3server:
#   pkg.purged:
#     - name: cortx-s3server

# #Remove s3server_uploads:
# #  pkg.purged:
# #    - pkgs:
# #      - python34-jmespath
# #      - python34-botocore
# #      - python34-s3transfer
# #      - python34-boto3
# #      - python34-xmltodict

# #Remove /tmp/s3certs:
# #  file.absent:
# #    - name: /tmp/s3certs

# #Delete directory /opt/s3server/ssl:
# #  file.absent:
# #    - name: /opt/seagate/s3server/ssl

# #Delete directory /opt/s3server/s3certs:
# #  file.absent:
# #    - name: /opt/seagate/s3server/s3certs

# #Remove working directory for S3 server:
# #  file.absent:
# #    - name: /var/seagate/s3

# Remove S3 and auth directory under opt:
#   file.absent:
#     - name: |
#         /opt/seagate/cortx/s3
#         /opt/seagate/cortx/auth

# #-------------------------
# # Teardown S3Server End
# #-------------------------

# #-------------------------
# # Teardown Common Runtime
# #-------------------------
# Remove common_runtime libraries:
#   pkg.purged:
#     - pkgs:
#       - java-1.8.0-openjdk-headless
#       - glog
#       - gflags
#       - yaml-cpp

# #------------------------------
# # Teardown Common Runtime End
# #------------------------------

# {% if salt['file.directory_exists']('/var/seagate/s3') %}
# Remove working directory for S3 server:
#   file.absent:
#     - name: /var/seagate/s3
# {% endif %}

# {% import_yaml 'components/defaults.yaml' as defaults %}

# Remove s3server_uploads repo:
#   pkgrepo.absent:
#     - name: {{ defaults.s3server.uploads_repo.id }}

# Remove s3server repo:
#   pkgrepo.absent:
#     - name: {{ defaults.s3server.repo.id }}

# Delete s3server checkpoint flag:
#   file.absent:
#     - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.s3server
