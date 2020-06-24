salt_minion_service_stopped:
  service.dead:
    - name: salt-minion
    - enable: False
