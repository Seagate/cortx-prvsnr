Setup keepalived master config (sample, manually updated):
  file.managed:
    - name: /etc/keepalived/keepalived.conf.master
    - source: salt://components/ha/keepalived/files/keepalived.conf.master
