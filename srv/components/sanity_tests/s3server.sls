{% if pillar['cluster'][grains['id']]['is_primary'] -%}
include:
  - components.s3clients

{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}
Run S3 Sanity tests:
  cmd.run:
    - name: /opt/seagate/s3/scripts/s3-sanity-test.sh 2>&1 | tee -a {{ logfile }}

{% endif %}
