{% macro repo_mounted(release, source, mount_dir) %}

eos_update_repo_iso_mounted_{{ release }}:
  mount.mounted:
    - name: {{ mount_dir }}
    - device: {{ source }}
    - mkmnt: True
    - fstype: iso9660
    - persist: False

{% endmacro %}
