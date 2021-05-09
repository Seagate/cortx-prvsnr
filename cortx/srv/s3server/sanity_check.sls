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

# Verify slapd port listens:
#   cmd.run:
#     - name: netstat -plnt | grep :$(grep -Po "(?<=ldapPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

#Verify slapd SSL port listens:
#  cmd.run:
#    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapSSLPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Verify HTTP port listens:
#   cmd.run:
#     - name: netstat -plnt | grep :$(grep -Po "(?<=httpPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Verify HTTPS port listens:
#   cmd.run:
#     - name: netstat -plnt | grep :$(grep -Po "(?<=httpsPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Test section is missing in /opt/seagate/cortx/s3/conf/setup.yaml
Stage - Test S3:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3:test')
