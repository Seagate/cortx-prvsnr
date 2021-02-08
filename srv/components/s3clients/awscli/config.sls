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

# Setup Credentials:
#   file.managed:
#     - name: ~/.aws/credentials
#     - source: salt://components/s3clients/awscli/files/.aws/credentials
#     - keep_source: False
#     - template: jinja
#     - makedirs: True
#     - replace: False
#     - create: True
#     - user: {{ grains['username'] }}
#     - group: {{ grains['groupname'] }}
#     - mode: 644

# Setup Configurations:
#   file.managed:
#     - name: ~/.aws/config
#     - source: salt://components/s3clients/awscli/files/.aws/config
#     - keep_source: False
#     - template: jinja
#     - makedirs: True
#     - replace: False
#     - create: True
#     - user: {{ grains['username'] }}
#     - group: {{ grains['groupname'] }}
#     - mode: 644
