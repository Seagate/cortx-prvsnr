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

{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Stage - Post Install S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3:post_install')
{% endif %}

# Update password in authserver.properties:
#   cmd.run:
#     - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['iam_admin']['secret']) }} -p /opt/seagate/auth/resources/authserver.properties
#     - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
#     - watch_in:
#       - service: s3authserver

Stage - Config S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3:config')

Stage - Init S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3:init')

