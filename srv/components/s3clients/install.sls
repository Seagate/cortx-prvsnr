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
