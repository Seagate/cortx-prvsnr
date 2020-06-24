include:
  - .install

Enable salt minion:
  service.enabled:
    - name: salt-minion
    - require:
      - Install Salt Minion

# REF: https://docs.saltstack.com/en/latest/faq.html#what-is-the-best-way-to-restart-a-salt-minion-daemon-using-salt-after-upgrade
Restart salt minion:
  cmd.run:
    - name: 'salt-call service.restart salt-minion'
    - bg: True
    - require:
      - Enable salt minion
