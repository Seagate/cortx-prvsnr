{% set node = grains['id'] %}

{%- if pillar['cluster'][node]['network']['data_if'] == 'lo' %}
Update lnet config file:
  test.fail_without_changes:
    - name: LNet doesn't support loopback network interface. Config dropped.
{% else %}
Update lnet config file:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
      - options lnet networks=tcp({{ salt['pillar.get']("cluster:{0}:network:data_if".format(node)) }})  config_on_load=1
    - user: root
    - group: root
{% endif %}

Update EOSCore config:
  module.run:
    - eoscore.conf_update:
      - name: /etc/sysconfig/mero
      - ref_pillar: eoscore
      - backup: True
