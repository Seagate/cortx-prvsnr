{% set node = grains['id'] %}

Update lnet config file:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
      - options lnet networks=tcp({{ salt['pillar.get']("cluster:{0}:network:data_if".format(node), 'lo') }})  config_on_load=1
    - user: root
    - group: root


Update EOSCore config:
  module.run:
    - eoscore.conf_update:
      - name: /etc/sysconfig/mero
      - ref_pillar: eoscore
      - backup: True
