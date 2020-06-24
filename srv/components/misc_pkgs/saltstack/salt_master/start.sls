include:
  - .install

salt_master_service_enabled:
  service.enabled:
    - name: salt-master
    - require:
      - install_salt_master

# Note. master restart is in foreground,
# so minion will reported to restarted master
salt_master_service_restarted:
  cmd.run:
    # 1. test.true will prevent restart of salt master if the config is malformed
    # 2. --local is required if salt-master is actually not running,
    #    since state might be called by salt-run as well
    - name: 'salt-run salt.cmd test.true && salt-call --local service.restart salt-master'
    - bg: True
    - require:
      - salt_master_service_enabled
