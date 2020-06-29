{% set chassis = salt['grains.get']('hostname_status', {}).get('Chassis', 'unknown') %}

{% if chassis == 'server' %}

include:
  - .install
  - .config

{% else %}

ipmi_configuration_skipped:
  test.nop:
    - name: chassis is {{ chassis }}

{% endif %}
