{% if pillar['cluster']['type'] == "ees" %}
include:
    - components.misc.openldap.config.replication
{% endif %}

Ensure sspl-ll running:
  service.running:
    - name: sspl-ll

Ensure halond running:
  service.running:
    - name: halond

Ensure HAProxy restarted:
  service.running:
    - name: haproxy
    - full_restart: True

Ensure Slapd restarted:
  service.running:
    - name: slapd
    - full_restart: True
    - watch_in:
      - service: Ensure s3authserver restarted

Ensure s3authserver restarted:
  service.running:
    - name: s3authserver
    - enable: True
    - full_restart: True
    - init_delay: 2

# TODO: Should be run only on primary node.
# Prereq: all the services on second node are online.
#{#% set node = grains['id'] %#}
#{#% if pillar['cluster'][node]['is_primary'] %#}
# hctl mero bootstrap
#Bootstrap mero:
#  cmd.run:
#    - name: hctl mero bootstrap
#    - onlyif: test -f /etc/halon/halon_facts.yaml
#    - require:
#      - service: Ensure halond running

# Expected running services
# s3authserver: running
# slapd: running
# haproxy: running
# halond: running
# sspl-ll: running
# mero-kernel: running
# lnet: dead running
#{#% endif %#}