{% import_yaml 'components/defaults.yaml' as defaults %}

{% set node = 'node_1' if grains['host'] == salt["pillar.get"]('facts:node_1:fqdn') else 'node_2' if grains['host'] == salt["pillar.get"]('facts:node_1:fqdn') else None %}

configure_lnet:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
      - options lnet networks=tcp({{ salt['pillar.get']("facts:{0}:data_if".format(node), 'lo') }})  config_on_load=1
    - user: root
    - group: root
