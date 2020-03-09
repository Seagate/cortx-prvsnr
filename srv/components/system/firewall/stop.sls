Stop and disable Firewalld service:
  service.dead:
    - name: firewalld
    - enable: False
