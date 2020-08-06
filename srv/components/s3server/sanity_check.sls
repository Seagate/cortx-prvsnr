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

Verify slapd port listens:
  cmd.run:
    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

#Verify slapd SSL port listens:
#  cmd.run:
#    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapSSLPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

Verify HTTP port listens:
  cmd.run:
    - name: netstat -plnt | grep :$(grep -Po "(?<=httpPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Verify HTTPS port listens:
#   cmd.run:
#     - name: netstat -plnt | grep :$(grep -Po "(?<=httpsPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Test section is missing in /opt/seagate/cortx/s3/conf/setup.yaml
# Stage - Test S3:
#   cmd.run:
#     - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:test')
