{% macro repo_mounted(release, source, mount_dir) %}

eos_update_iso_repo_mounted_{{ release }}:
  mount.mounted:
    - name: {{ mount_dir }}
    - device: {{ source }}
    - mkmnt: True
    - fstype: iso9660
    - persist: True

{% endmacro %}
