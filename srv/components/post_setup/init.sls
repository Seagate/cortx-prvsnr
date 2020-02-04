Service HAProxy running:
  service.running:
    - name: haproxy

Service slapd running:
  service.running:
    - name: slapd

Service s3authserver running:
  service.running:
    - name: s3authserver
    - enable: True
    - init_delay: 2

include:
  - components.hare.start

# Expected running services
# s3authserver: running
# slapd: running
# haproxy: running
# halond: running
# sspl-ll: running
# mero-kernel: running
# lnet: dead running
