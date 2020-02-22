{% macro repo_absent(release, mount_dir) %}

    {% from './iso/unmount.sls' import repo_unmounted with context %}

{{ repo_unmounted(release, mount_dir) }}

eos_update_repo_absent_{{ release }}:
  pkgrepo.absent:
    - name: eos_update_{{ release }}
    - require_in:
      - sls: eos_update_iso_repo_unmounted_{{ release }}


{% endmacro %}
