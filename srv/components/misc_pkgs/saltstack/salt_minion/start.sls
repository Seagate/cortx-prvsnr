include:
  - .config

salt_minion_service_enabled:
  service.enabled:
    - name: salt-minion
    - require:
      - file: salt_minion_config_updated

salt_minion_service_restarted:
  cmd.run:
    - name: 'salt-call service.restart salt-minion'
    - bg: True
    - onchanges:
      - file: salt_minion_config_updated
