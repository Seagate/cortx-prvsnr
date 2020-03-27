Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:post_install')

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:config')

Conul entry for controller details:
  cmd.run:
    - names:
      - consul kv put sspl.STORAGE_ENCLOSURE.primary_controller_ip {{ pillar["cluster"]["storage_enclosure"]["controller"]["primary_mc"]["ip"] }}
      - consul kv put sspl.STORAGE_ENCLOSURE.primary_controller_port {{ pillar["cluster"]["storage_enclosure"]["controller"]["primary_mc"]["port"] }}
      - consul kv put sspl.STORAGE_ENCLOSURE.user {{ pillar["cluster"]["storage_enclosure"]["controller"]["user"] }}
      - consul kv put sspl.STORAGE_ENCLOSURE.password {{ pillar["cluster"]["storage_enclosure"]["controller"]["password"] }}
        

{% if pillar["cluster"][grains["id"]]["is_primary"] %}
#run health schema on master for both node and enclosure and for minion only for node health.
Run Health Schema on master:
  cmd.run:
    - name: resource_health_view -ne --path "/tmp/resource_health_view.json"

Merge healthschema:
  module.run:
    - sspl.health_map_schema:
      - file_path: "/tmp/resource_health_view.json"

{% elseif %}
Run Health Schema on minion:
  cmd.run:
    - name: resource_health_view -n --path "/tmp/resource_health_view.json"
{% endif %}
 

Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:init')
