{% macro repo_added(release, source, mount_dir) %}

    {% from './iso/mount.sls' import repo_mounted with context %}

    {% if source.endswith('.iso') %}
{{ repo_mounted(release, source, mount_dir) }}
    {% endif %}

eos_update_repo_added_{{ release }}:
  pkgrepo.managed:
    - name: eos_update_{{ release }}
    - humanname: EOS Update repo {{ release }}
        {% if source.endswith('.iso') %}
    - baseurl: file://{{ mount_dir }}
    - require:
      - eos_update_iso_repo_mounted_{{ release }}
        {% else %}
    - baseurl: {{ source }}
        {% endif %}
    - gpgcheck: 0


eos_update_repo_metadata_cleaned_{{ release }}:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="eos_update_{{ release }}" clean metadata


{% endmacro %}
