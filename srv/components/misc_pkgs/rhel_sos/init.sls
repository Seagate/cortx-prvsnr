{% if "RedHat" in grains['os'] %}
include:
  - .prepare
  - .install
  - .config
{% endif %}
