include:
  - .stop

remove_salt_minion:
  pkg.purge:
    - name: salt-minion
    - require:
      - salt_minion_service_stopped
