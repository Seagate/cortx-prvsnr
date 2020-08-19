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

{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Stage - Post Install S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:post_install')
{% endif %}

# Update password in authserver.properties:
#   cmd.run:
#     - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['iam_admin']['secret']) }} -p /opt/seagate/auth/resources/authserver.properties
#     - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
#     - watch_in:
#       - service: s3authserver

Stage - Config S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:config')

Stage - Init S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:init')

Append /etc/hosts:
  file.line:
    - name: /etc/hosts
    - content: {{ pillar['cluster']['cluster_ip'] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
    - location : end
    - mode: insert
