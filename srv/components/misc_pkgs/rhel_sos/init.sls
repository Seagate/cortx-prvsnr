{% if "RedHat" in grains['os'] %}
include:
  - .prepare
  - .install
  - .config
{% else %}
No HA cleanup for CSM:
  test.show_notification:
      - text: "SOS is not required for Non RedHat systems, skipping.."
{% endif %}
