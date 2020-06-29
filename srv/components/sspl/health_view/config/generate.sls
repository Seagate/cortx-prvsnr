include:
  - components.sspl.install
  - components.sspl.config.commons

{% set enclosure = '' %}
{% if "primary" in grains["roles"] %}
# run health schema on master for both node and enclosure; on minion only for node health.
{% set enclosure = '-e' %}
{% endif %}
Run Resource Health View:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n {{ enclosure }} --path /tmp
    - require:
      - Install cortx-sspl packages
      - Add common config - system information to Consul
      - Add common config - rabbitmq cluster to Consul
      - Add common config - BMC to Consul
      - Add common config - storage enclosure to Consul
