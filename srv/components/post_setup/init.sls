Ensure halond running:
  service.running:
    - name: halond

{% set node = grains['id'] %}
{% if pillar['cluster'][node]['is_primary'] %}
# hctl mero bootstrap
Bootstrap mero:
  cmd.run:
    - name: hctl mero bootstrap
    - onlyif: test -f /etc/halon/halon_facts.yaml
    - require:
      - service: Ensure halond running

Restart HAProxy:
  service.running:
    - name: haproxy
{% endif %}

# Expected running services
# s3authserver: running
# slapd: running
# haproxy: running
# halond: running
# sspl-ll: running
# mero-kernel: running
# lnet: dead running
