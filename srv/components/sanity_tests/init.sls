{% if pillar['cluster'][grains['id']]['is_primary'] -%}

{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}
Create log file:
  file.touch:
    - name: {{ logfile }}

include:
  - .s3server
  - .csm
  - .sspl

{% endif %}
