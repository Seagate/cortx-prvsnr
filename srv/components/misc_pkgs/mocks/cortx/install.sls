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

/usr/local/bin/mock:
  file.managed:
    - source: salt://components/misc_pkgs/mocks/cortx/files/scripts/mock.py
    - user: root
    - group: root
    - mode: 755
    - makedirs: True


cortx_mock_pkgs_installed:
  pkg.installed:
    - pkgs:
{% for pkg_name, pkg_ver in salt['pillar.get']('commons:version:cortx').items() %}
    {% if pkg_name not in ('cortx-prvsnr', 'python36-cortx-prvsnr') %}
      - {{ pkg_name }}: {{ pkg_ver }}
    {% endif %}
{% endfor %}
    - refresh: True
