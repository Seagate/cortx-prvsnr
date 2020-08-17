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

Install requisites:
  pkg.installed:
    - pkgs:
      - python36-boto3
      - python36-botocore
      - python36-jmespath
      - python36-s3transfer
      - python36-xmltodict

# Install certs:
#   pkg.installed:
#     - sources:
#       - stx-s3-client-certs: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

Install cortx-s3iamcli:
  pkg.installed:
    - pkgs:
      - cortx-s3iamcli: latest
#       # - cortx-s3iamcli-devel
