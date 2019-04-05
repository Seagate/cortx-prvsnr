include:
  - components.halon.install

{% import_yaml 'components/defaults.yaml' as defaults %}

lnet_conf:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    # TODO: data0 should be identified from the system and not hard-coded value.
    # TODO: For infiniband network tcp value changes to ib
    - contents: |
        options lnet networks=tcp(data0) config_on_load=1
    - user: root
    - group: root

halon_conf:
  file.managed:
    - name: /etc/sysconfig/halond
    - contents: |
        HALOND_LISTEN={{ defaults.halon.rc_listen.ip }}:{{ defaults.halon.rc_listen.port }}
    - user: root
    - group: root

halon_service:
  service.running:
    - name: halond
    - enable: True
    - watch:
      - file: halon_conf
