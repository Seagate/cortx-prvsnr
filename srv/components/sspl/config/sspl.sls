
include:
  - .commons

Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:post_install')
    - require:
      - Add common config - system information to Consul
      - Add common config - rabbitmq cluster to Consul
      - Add common config - BMC to Consul
      - Add common config - storage enclosure to Consul

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:config')
    - require:
      - Stage - Post Install SSPL

{% if "physical" in grains['virtual'] %}
{% if pillar["cluster"][grains["id"]]["is_primary"] %}
# run health schema on master for both node and enclosure and for minion only for node health.
Run Health Schema:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n -e --path "/tmp/"
    - requrie:
      - Stage - Configure SSPL

{% if 'ees' in pillar['cluster']['type'] %}
Merge healthschema:
  module.run:
    - sspl.health_map_schema:
      - healthmap_path: {{ pillar["sspl"]["healthmappath"] }}
    - require:
      - Run Health Schema
{% endif %}

{% else %}
Run Health Schema:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n --path "/tmp/"
    - require:
      - Stage - Configure SSPL
{% endif %}
{% endif %} 

Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:init')
