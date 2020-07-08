{% from './install.sls' import repo_added with context %}
{% from './teardown.sls' import repo_absent with context %}

{% for release, source in pillar['eos_release']['update']['repos'].items() %}

    {% set repo_dir = '/'.join(
        [pillar['eos_release']['update']['base_dir'], release]) %}

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


{% if not pillar['eos_release']['update']['repos'] %}

sw_update_no_repos:
  test.nop: []

{% endif %}
