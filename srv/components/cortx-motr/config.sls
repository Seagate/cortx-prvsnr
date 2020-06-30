{% if "physical" in grains['virtual'] %}
# Override CortxMotr config from pillar data:
#   module.run:
#     - cortxmotr.conf_update:
#       - name: /etc/sysconfig/mero
#       - ref_pillar: cortx-motr
#       - backup: True
{% endif %}

Stage - Post Install Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:post_install')

Stage - Config Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:config')

Stage - Init CortxMotr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:init')
