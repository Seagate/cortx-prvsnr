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

{% from './_macros.sls' import setup_repos with context %}

{% set base_dir = pillar['release']['upgrade']['base_dir'] %}

{% for version, repos in pillar['release']['upgrade']['repos'].items() %}

    {% set single_iso_repo = {version: repos.pop(version, None)} %}

    { % if single_iso_repo[version] % }

    # to mount the single ISO first
    { { setup_repos(single_iso_repo, base_dir) } }

    { % endif % }

    {% set upgrade_repos = dict() %}
    {% for release in repos %}
    {% set key =  'sw_upgrade_' ~ release ~ '_' ~ version %}
    {% set _dummy = upgrade_repos.update({key: repos[release]}) %}
    {% endfor %}

    {{ setup_repos(upgrade_repos, base_dir) }}

{% endfor %}
