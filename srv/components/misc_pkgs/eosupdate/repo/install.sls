{% macro repo_added(release, source, source_type) %}

    {% from './iso/mount.sls' import repo_mounted with context %}

    {% if source_type == 'iso' %}

        {% set iso_path = source + '.iso' %}

copy_repo_iso:
  file.managed:
    - name: {{ iso_path }}
    - source: salt://misc_pkgs/eosupdate/repo/files/{{ release }}.iso
    - require_in:
      - eos_update_repo_iso_mounted_{{ release }}
      - eos_update_repo_added_{{ release }}


{{ repo_mounted(release, iso_path, source) }}

    {% elif source_type == 'dir' %}


copy_repo_dir:
  file.recurse:
    - name: {{ source }}
    - source: salt://misc_pkgs/eosupdate/repo/files/{{ release }}
    - require_in:
      - eos_update_repo_added_{{ release }}


    {% endif %}


eos_update_repo_added_{{ release }}:
  pkgrepo.managed:
    - name: eos_update_{{ release }}
    - humanname: EOS Update repo {{ release }}
    {% if source_type == 'url' %}
    - baseurl: {{ source }}
    {% else %}
    - baseurl: file://{{ source }}
    {% endif %}
    - gpgcheck: 0
    {% if source_type == 'iso' %}
    - require:
      - eos_update_repo_iso_mounted_{{ release }}
    {% endif %}


eos_update_repo_metadata_cleaned_{{ release }}:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="eos_update_{{ release }}" clean metadata
    - require:
      - eos_update_repo_added_{{ release }}

{% endmacro %}
