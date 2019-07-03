{% import_yaml 'components/defaults.yaml' as defaults %}

{% if salt['service.status']('halond.service') %}
Stop cluster:
  cmd.run:
    - name: hctl mero stop

Cleanup halon:
  service.running:
    - name: halon-cleanup
{% endif %}

# This sercice should already be stooped by halon-cleanup above
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
