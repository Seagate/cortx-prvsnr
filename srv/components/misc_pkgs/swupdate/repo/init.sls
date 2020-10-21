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

{% from './install.sls' import repo_added with context %}
{% from './teardown.sls' import repo_absent with context %}

{% for release, source in pillar['release']['update']['repos'].items() %}

    {% set repo_dir = '/'.join(
        [pillar['release']['update']['base_dir'], release]) %}
    {% set repo_params = {} %}

    {% if source %}

        {% if source is mapping %}
            {% set repo_params = source.get('params', {}) %}
            {% set source = source['source'] %}
        {% endif %}


        {% if source.startswith(('http://', 'https://')) %}

            {% set source_type = 'url' %}

        {% elif source in ('iso', 'dir')  %}

            {% set source_type = source %}
            {% set source = repo_dir %}

        {% else  %}

unexpected_repo_source:
  test.fail_without_changes:
    - name: {{ source }}

        {% endif %}

{{ repo_added(release, source, source_type, repo_params) }}

    {% else %}

{{ repo_absent(release, repo_dir) }}

    {% endif %}

{% endfor %}


{% if not pillar['release']['update']['repos'] %}

sw_update_no_repos:
  test.nop: []

{% endif %}
