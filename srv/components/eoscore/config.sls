{% if "physical" in grains['virtual'] %}
Override EOSCore config from pillar data:
  module.run:
    - eoscore.conf_update:
      - name: /etc/sysconfig/mero
      - ref_pillar: eoscore
      - backup: True
{% endif %}

Stage - Post Install Core:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/core/conf/setup.yaml', 'core:post_install')

Stage - Config Core:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/core/conf/setup.yaml', 'core:config')

Stage - Init EOSCore:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/core/conf/setup.yaml', 'core:init')
