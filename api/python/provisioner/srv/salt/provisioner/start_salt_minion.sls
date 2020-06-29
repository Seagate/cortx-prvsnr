salt_minion_running:
  service.running:
    - name: salt-minion.service
