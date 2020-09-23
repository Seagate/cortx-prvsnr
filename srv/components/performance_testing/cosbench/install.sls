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

Install support packages:
  pkg.installed:
      - pkgs:
        - java-1.8.0-openjdk-headless.x86_64
        - nmap-ncat.x86_64

Download and extract cosbench:
  archive.extracted:
    - name: /opt
    - source: https://github.com/intel-cloud/cosbench/releases/download/v0.4.2.c3/0.4.2.c3.zip
    - keep_source: False
    - skip_verify: True
    - force: True
    - overwrite: True
    - clean: True

Rename file:
  file.rename:
    - name: /opt/cos
    - source: /opt/0.4.2.c3
    - makedirs: True
    - force: True
    - require:
      - archive: Download and extract cosbench
