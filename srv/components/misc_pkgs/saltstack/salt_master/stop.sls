salt_master_service_stopped:
  service.dead:
    - name: salt-master
    - enable: False
