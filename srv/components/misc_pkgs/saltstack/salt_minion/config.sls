include:
  - .install

salt_minion_config_updated:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://components/misc_pkgs/saltstack/salt_minion/files/minion
    - template: jinja
    - require:
      - install_salt_minion
