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

{% for release, source in pillar['release']['upgrade']['repos'].items() %}

    {% set repo_dir = '/'.join(
        [pillar['release']['upgrade']['base_dir'], release]) %}
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

{% from './iso/mount.sls' import repo_mounted with context %}

    {% if source_type == 'iso' %}

        {% set iso_path = source + '.iso' %}

copy_repo_iso_{{ release }}:
  file.managed:
    - name: {{ iso_path }}
    - source: salt://misc_pkgs/swupgrade/repo/files/{{ release }}.iso
    - makedirs: True
    - require_in:
      - sw_upgrade_repo_iso_mounted_{{ release }}


{{ repo_mounted(release, iso_path, source) }}

    {% elif source_type == 'dir' %}


copy_repo_dir_{{ release }}:
  file.recurse:
    - name: {{ source }}
    - source: salt://misc_pkgs/swupgrade/repo/files/{{ release }}

    {% endif %}

{# TODO: Get YUM repos directly from mount dir #}
{% for repo_name in ('3rd_party', 'cortx_iso', 'os') %}

{{ repo_added(release, source, source_type, repo_name, repo_params) }}

{% endfor %}

    {% else %}

{{ repo_absent(release, repo_dir) }}

    {% endif %}

{% endfor %}


{% if not pillar['release']['upgrade']['repos'] %}

sw_upgrade_no_repos:
  test.nop: []

{% endif %}
