# hctl mero bootstrap
bootstrap mero:
  cmd.run:
    - name: hctl mero bootstrap
    - onlyif: test -f /etc/halon/halon_facts.yaml

# Expected running services
# s3authserver: Failed
# slapd: running
# haproxy: failed
# lnet: dead (disabled)
# halond: running
# sspl-ll: running
# mero-kernel: dead (disabled)
