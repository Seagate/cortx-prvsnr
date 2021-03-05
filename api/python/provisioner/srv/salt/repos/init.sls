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


# TODO DRY EOS-12076 it's a copy-paste
#      of misc_pkgs/swupdate/repo from core

{% from './install.sls' import repo_added with context %}
{% from './teardown.sls' import repo_absent with context %}

{% set default_install_type = 'base' %}
{% set install_type = salt['pillar.get']('release:install_type', default_install_type) %}

{% for release, source in pillar['release'][install_type]['repos'].items() %}

    {% set source_type = None %}
    {% set is_repo = True %}
    {% set repo_dir = '/'.join(
        [pillar['release'][install_type]['base_dir'], release]) %}

    {% if source %}

        {% if source is mapping %}
            {% set is_repo = source['is_repo'] | to_bool %}
            {% set source = source['source'] %}
        {% endif %}

        {% if source.startswith(('http://', 'https://', 'file://')) %}

            {% set source_type = 'url' %}

        # TODO TEST EOS-12076
        {% elif source.startswith('salt://') %}

            {% if source.endswith('.iso')  %}

                {% set source_type = 'iso' %}

            {% else  %}

                {% set source_type = 'dir' %}

            {% endif %}

        {% elif source in ('iso', 'dir')  %}

            {% set source_type = source %}
            {% set source = (
                    "salt://{}{}".format(
                        release,  '.iso' if source == 'iso' else ''
                    )
               )
            %}

        {% else  %}

unexpected_repo_source:
  test.fail_without_changes:
    - name: {{ source }}

        {% endif %}  # source value inspection

{{ repo_added(release, source, source_type, repo_dir, is_repo) }}

    {% else %}  # source is undefined

{{ repo_absent(release, repo_dir) }}

    {% endif %} # source inspection

{% endfor %}


{% if not pillar['release'][install_type]['repos'] %}

no_repos:
  test.nop: []

{% endif %}
