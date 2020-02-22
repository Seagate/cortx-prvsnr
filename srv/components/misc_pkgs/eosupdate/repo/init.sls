{% from './install.sls' import repo_added with context %}
{% from './teardown.sls' import repo_absent with context %}

{% for release, source in pillar['eos_release']['update']['repos'].items() %}

    {% set mount_dir = '/'.join([pillar['eos_release']['update']['mount_base_dir'], release]) %}

    {% if source %}

{{ repo_added(release, source, mount_dir) }}

    {% else %}

{{ repo_absent(release, mount_dir) }}

    {% endif %}

{% endfor %}


{% if not pillar['eos_release']['update']['repos'] %}

eos_update_no_repos:
  test.nop: []

{% endif %}
