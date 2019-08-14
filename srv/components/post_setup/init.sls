{% set node = grains['id'] %}

{% if pillar['cluster'][node]['is_primary'] %}

Ensure halond running:
  service.running:
    - name: halond

Restart HAProxy:
  service.running:
    - name: haproxy
    - watch:
      - cmd: Bootstrap mero

# hctl mero bootstrap
Bootstrap mero:
  cmd.run:
    - name: hctl mero bootstrap
    - onlyif: test -f /etc/halon/halon_facts.yaml
    - require:
      - service: Ensure halond running

# Expected running services
# s3authserver: Failed
# slapd: running
# haproxy: failed
# lnet: dead (disabled)
# halond: running
# sspl-ll: running
# mero-kernel: dead (disabled)

{% endif %}
