{% import_yaml 'components/defaults.yaml' as defaults %}

configure_lnet:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
      - options lnet networks=tcp({{ defaults.mero.config.lnet_dev }})  config_on_load=1
    - user: root
    - group: root
