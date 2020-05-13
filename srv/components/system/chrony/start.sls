enable chrony service:
  service.running:
    - enable: true
    - name: chronyd
