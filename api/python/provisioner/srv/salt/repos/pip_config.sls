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

{% set python_repo_path = pillar['release']['python_repo'] %}

configure pip:
  file.managed:
    - name: /etc/pip.conf
    - contents: |
        [global]
        timeout: 60
        index-url: {{ python_repo_path }}
{%- if python_repo_path.startswith(('http://', 'https://')) %}
        trusted-host: {{ python_repo_path.split('/')[2] }}
{%- endif -%}
