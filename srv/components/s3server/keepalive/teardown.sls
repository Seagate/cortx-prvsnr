remove keepalived config:
  file.absent:
    - name: /etc/keepalived/keepalived.conf

Purge keepalived:
  pkg.purge:
    - name: keepalived
