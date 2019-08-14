Remove keepalived config:
  file.absent:
    - name: /etc/keepalived/keepalived.conf

Remove keepalived master config:
  file.absent:
    - name: /etc/keepalived/keepalived.conf.master

Purge keepalived:
  pkg.purged:
    - name: keepalived
