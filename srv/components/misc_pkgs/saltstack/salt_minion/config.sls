include:
  - .install
  - .start

Salt minion config updated:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://components/misc_pkgs/saltstack/salt_minion/files/minion
    - template: jinja
    - require:
      - Install Salt Minion
    - onchanges_in:
      - Restart salt minion
