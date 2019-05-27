{% import_yaml 'components/defaults.yaml' as defaults %}

disable_halon_service:
  service.dead:
    - name: halond
    - enable: false

delete_halon_conf:
  file.absent:
    - name: /etc/sysconfig/halond
