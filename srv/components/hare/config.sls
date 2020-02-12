{% for hare_service in ('hare-hax.service', 'hare-consul-agent.service') %}
{% if not salt['service.status']( hare_service ) %}
Resetting failed {{ hare_service }}:
  cmd.run:
    - name: systemctl reset-failed {{ hare_service }}
{% endif %}
{% endfor %}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Stage - Post Install Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:post_install')

Stage - Configure Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:config')

Stage - Initialize Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:init')
{% endif %}
