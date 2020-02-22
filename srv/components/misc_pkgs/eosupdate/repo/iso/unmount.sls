{% macro repo_unmounted(release, mount_dir) %}

eos_update_iso_repo_unmounted_{{ release }}:
  mount.unmounted:
    - name: {{ mount_dir }}
    - persist: True

eos_update_iso_repo_mount_dir_absent_{{ release }}:
  file.absent:
    - name: {{ mount_dir }}
    - require:
      - eos_update_iso_repo_unmounted_{{ release }}

{% endmacro %}
