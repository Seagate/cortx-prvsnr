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

# Configure s3cmd:
#   file.managed:
#     - name: ~/.s3cfg
#     - source: salt://components/s3clients/s3cmd/files/.s3cfg
#     - keep_source: False
#     - template: jinja
#     - makedirs: True
#     - replace: False
#     - create: True
#     - user: {{ salt['grains.get']('username') }}
#     - group: {{ salt['grains.get']('groupname') }}
#     - mode: 644

# Create directory for s3cmd ssl certs:
#   file.directory:
#     - name: ~/.s3cmd/ssl
#     - makedirs: True
#     - clean: True
#     - force: True

# Copy certs:
#   file.copy:
#     - name: ~/.s3cmd/ssl/ca.crt
#     - source: /etc/ssl/stx-s3-clients/s3/ca.crt
#     - makedirs: True
#     - preserve: True
