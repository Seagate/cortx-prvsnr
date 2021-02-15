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

# TODO: use path from pillars or any other configuration
{% set mocks_repo = '/var/lib/seagate/cortx/provisioner/local/cortx_repos/deploy_cortx_mock' %}
{% set salt_root = '/opt/seagate/cortx/provisioner/srv' %}

{{ mocks_repo }}:
  file.directory:
    - mode: 755
    - makedirs: True

build_mock_repo:
  cmd.run:
    - name: bash {{ salt_root }}/{{ tpldir }}/files/scripts/buildbundle.sh -o {{ mocks_repo }} -t deploy-cortx -r 1.0.0 -vv
    - creates: {{ mocks_repo }}/repodata
    - require:
      - file: {{ mocks_repo }}

Stage - Install CORTX mock repo:
  pkgrepo.managed:
    - name: cortx_mock_repo
    - humanname: CORTX Mock repo
    - baseurl: file://{{ mocks_repo }}
    - enabled: True
    - gpgcheck: 0
    - require:
      - build_mock_repo


/usr/local/bin/mock:
  file.managed:
    - source: salt://components/misc_pkgs/mocks/cortx/files/scripts/mock.py
    - user: root
    - group: root
    - mode: 755
    - makedirs: True
