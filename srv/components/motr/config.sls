{% if "physical" in grains['virtual'] %}
# Override Motr config from pillar data:
#   module.run:
#     - motr.conf_update:
#       - name: /etc/sysconfig/motr
#       - ref_pillar: motr
#       - backup: True
{% endif %}

Stage - Post Install Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:post_install')

Stage - Config Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:config')

Stage - Init Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:init')
