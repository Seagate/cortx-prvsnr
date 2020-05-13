include:
  - components.misc_pkgs.openldap.config.base
{% if pillar['cluster']['type'] != "single" %}
  - components.misc_pkgs.openldap.config.replication
{% endif %}
