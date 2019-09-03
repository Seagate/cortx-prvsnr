{% set node = grains['id'] %}
{% if pillar['cluster']['type'] == "ees" and pillar['cluster'][node]['is_primary'] == True %}
include:
  - components.halon.config.generate_facts
{% endif %}
Ensure sspl-ll running:
  service.running:
    - name: sspl-ll

Ensure halond running:
  service.running:
    - name: halond

Ensure HAProxy running:
  service.running:
    - name: haproxy

Ensure Slapd running:
  service.running:
    - name: slapd

Ensure s3authserver running:
  service.running:
    - name: s3authserver
    - enable: True
    - init_delay: 2

# TODO: Should be run only on primary node.
# Prereq: for ees all the services on second node are online.
{% if pillar['cluster'][node]['is_primary'] == True %}
Bootstrap mero:
 cmd.run:
   - name: hctl mero bootstrap
   - onlyif: test -f /etc/halon/halon_facts.yaml && test -f /etc/halon/bootstrap.ready
   - require:
     - service: Ensure halond running
{% endif %}}

# Expected running services
# s3authserver: running
# slapd: running
# haproxy: running
# halond: running
# sspl-ll: running
# mero-kernel: running
# lnet: dead running
