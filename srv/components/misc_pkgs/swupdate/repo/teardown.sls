{% macro repo_absent(release, repo_dir) %}

    {% from './iso/unmount.sls' import repo_unmounted with context %}

{{ repo_unmounted(release, repo_dir) }}

sw_update_repo_iso_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}.iso
    - require:
      - sw_update_repo_iso_unmounted_{{ release }}


sw_update_repo_dir_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}
    - require:
      - sw_update_repo_absent_{{ release }}
      - sw_update_repo_iso_unmounted_{{ release }}


sw_update_repo_absent_{{ release }}:
  pkgrepo.absent:
    - name: sw_update_{{ release }}

{% endmacro %}
