{% macro repo_unmounted(release, mount_dir) %}

eos_update_repo_iso_unmounted_{{ release }}:
  mount.unmounted:
    - name: {{ mount_dir }}
    - persist: True

{% endmacro %}
