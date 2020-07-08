{% macro repo_unmounted(release, mount_dir) %}

sw_update_repo_iso_unmounted_{{ release }}:
  mount.unmounted:
    - name: {{ mount_dir }}
    - persist: True

{% endmacro %}
