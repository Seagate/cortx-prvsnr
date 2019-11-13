include:
  - components.misc.openldap.config.base
{% if pillar['cluster']['type'] != "single" %}
  - components.misc.openldap.config.replication
{% endif %}