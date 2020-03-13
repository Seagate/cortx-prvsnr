Start and enable Firewalld service:
  service.running:
    - name: firewalld
    - enable: True
    - reload: True
