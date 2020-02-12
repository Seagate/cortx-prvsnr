{%- if pillar['cluster'][grains['id']]['network']['data_if'] == 'lo' %}
Update lnet config file:
  test.fail_without_changes:
    - name: LNet doesn't support loopback network interface. Config dropped.

{% else %}

Update lnet config file:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
{% if salt['cmd.retcode']('lspci | grep "Ethernet controller: Mellanox Technologies MT27800 Family"') %}
      - options lnet networks=o2ib({{ salt['pillar.get']("cluster:{0}:network:data_if".format(grains['id'])) }})  config_on_load=1
{% else %}
      - options lnet networks=tcp({{ salt['pillar.get']("cluster:{0}:network:data_if".format(grains['id'])) }})  config_on_load=1
{% endif %}
    - user: root
    - group: root

{% endif %}
