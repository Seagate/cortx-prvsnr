{% import_yaml 'components/defaults.yaml' as defaults %}

{% if salt['service.status']('halond.service') %}
Cleanup halon:                # Does 'hctl mero stop'
  service.running:
    - name: halon-cleanup

# This sercice should already be stoped by halon-cleanup above
Disable Halon service:
  service.dead:
    - name: halond
    - enable: false
{% endif %}

{% if salt['ps.pgrep']('m0d') -%}
Kill m0d process:
  module.run:
    - ps.pkill:
      - pattern: m0d
      - signal: 9             # Force kill the processes
{%- endif %}

{% if salt['ps.pgrep']('s3server') -%}
Kill s3server process:
  module.run:
    - ps.pkill:
      - pattern: s3server
      - signal: 9             # Force kill the processes
{%- endif %}

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

Remove bootstrap.ready file:
  file.absent:
    - name: /etc/halon/bootstrap.ready
    - onlyif: test -f /etc/halon/bootstrap.ready
