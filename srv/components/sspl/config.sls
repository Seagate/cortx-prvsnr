Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:post_install')

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:config')

{% if "physical" in grains['virtual'] %}
{% if pillar["cluster"][grains["id"]]["is_primary"] %}
# run health schema on master for both node and enclosure and for minion only for node health.
Run Health Schema on master:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n -e --path "/tmp/"

{% if 'ees' in pillar['cluster']['type'] %}
Merge healthschema:
  module.run:
    - sspl.health_map_schema:
      - healthmap_path: {{ pillar["sspl"]["healthmappath"] }}

{% else %}
Run Health Schema on minion:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n --path "/tmp/"
{% endif %}
{% endif %} 
Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:init')
