{% macro repo_absent(release, repo_dir) %}

    {% from './iso/unmount.sls' import repo_unmounted with context %}

{{ repo_unmounted(release, repo_dir) }}

eos_update_repo_iso_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}.iso
    - require:
      - eos_update_repo_iso_unmounted_{{ release }}


eos_update_repo_dir_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}
    - require:
      - eos_update_repo_absent_{{ release }}
      - eos_update_repo_iso_unmounted_{{ release }}


eos_update_repo_absent_{{ release }}:
  pkgrepo.absent:
    - name: eos_update_{{ release }}

{% endmacro %}
