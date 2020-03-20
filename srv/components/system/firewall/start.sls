Start and enable firewalld service:
  service.running:
    - name: firewalld
    - enable: True
    - reload: True
