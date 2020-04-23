Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:post_install')

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:config')

{% if pillar["cluster"][grains["id"]]["is_primary"] %}
# Run Health Schema on minion:
#   cmd.run:
#     - name: /opt/seagate/eos/sspl/lib/resource_health_view -n --path "/tmp/"

# run health schema on master for both node and enclosure and for minion only for node health.
Run Health Schema on master:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n -e --path "/tmp/"

Merge healthschema:
  module.run:
    - sspl.health_map_schema:
      - file_path: "/tmp/resource_health_view.json"

{% else %}
Run Health Schema on minion:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n --path "/tmp/"
{% endif %}
 
Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:init')
