include:
  - .stop

remove_salt_master:
  pkg.purge:
    - name: salt-master
    - require:
      - salt_master_service_stopped
