#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

{% from './install.sls' import repo_added with context %}
{% from './teardown.sls' import repo_absent with context %}

{% for release, source in pillar['release']['update']['repos'].items() %}

    {% set repo_dir = '/'.join(
        [pillar['release']['update']['base_dir'], release]) %}

    {% if source %}

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

{{ repo_added(release, source, source_type) }}

    {% else %}

{{ repo_absent(release, repo_dir) }}

    {% endif %}

{% endfor %}


{% if not pillar['release']['update']['repos'] %}

sw_update_no_repos:
  test.nop: []

{% endif %}
