{% import_yaml 'components/defaults.yaml' as defaults %}

Disable Halon service:
  service.dead:
    - name: halond
    - enable: false

Remove Halon package:
  pkg.purged:
    - pkgs:
      - halon

Delete Halon conf file:
  file.absent:
    - name: /etc/sysconfig/halond

Remove temporary mini_conf file:
  file.absent:
    - name: /tmp/mini_conf.yaml

Remove temporary halon_facts file:
  file.absent:
    - name: /tmp/halon_facts.yaml
