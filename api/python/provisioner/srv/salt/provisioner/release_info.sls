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

# TODO IMPROVE EOS-8473 move to pillar to make configurable
{% set dist_type = pillar['release']['type'] %}
{% set target_build = pillar['release']['target_build'] %}
{% set url = target_build %}
{% set release_file = '/etc/yum.repos.d/RELEASE_FACTORY.INFO' %}

{% if dist_type == 'bundle' %}
    {% set url += "/cortx_iso" %}
{% endif %}

{% if url.startswith(('http://', 'https://')) %}

{{ release_file }}:
  cmd.run:
      - name: curl {{ url }}/RELEASE.INFO -o {{ release_file }}
      - creates: {{ release_file }}

{% elif url.startswith('file://') %}

{{ release_file }}:
  file.managed:
      - source: {{ url[7:] }}/RELEASE.INFO

{% else %}

{{ release_file }}:
  test.fail_without_changes:
    - name: 'Unexpected target build: ' {{ target_build }}

{% endif %}
