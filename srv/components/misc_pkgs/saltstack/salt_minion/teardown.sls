include:
  - .stop

remove_salt_minion:
  pkg.purged:
    - name: salt-minion
    - require:
      - salt_minion_service_stopped
