include:
  - .stop

remove_salt_master:
  pkg.purged:
    - name: salt-master
    - require:
      - salt_master_service_stopped
