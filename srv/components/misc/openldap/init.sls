include:
  - components.misc.openldap.prepare
  - components.misc.openldap.install
  - components.misc.openldap.config.base
{% if pillar['cluster']['type'] == "ees" %}
  - components.misc.openldap.config.replication
{% endif %}
  - components.misc.openldap.housekeeping
  - components.misc.openldap.sanity_check