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

/root/.ssh:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - makedirs: True
    - force: True
    - recurse:
      - user
      - group
      - mode

/root/.ssh/id_rsa:
  file.managed:
    - source: salt://components/system/files/.ssh/id_rsa_prvsnr
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 600
    - create: True

/root/.ssh/id_rsa.pub:
  file.managed:
    - source: salt://components/system/files/.ssh/id_rsa_prvsnr.pub
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True

/root/.ssh/authorized_keys:
  file.managed:
    - source: salt://components/system/files/.ssh/authorized_keys
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True

/root/.ssh/known_hosts:
  file.managed:
    - source: salt://components/system/files/.ssh/known_hosts
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True
    - template: jinja
