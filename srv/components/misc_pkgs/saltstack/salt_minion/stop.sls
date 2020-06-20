salt_minion_service_stopped:
  service.deaf:
    - name: salt-minion
    - enable: False
