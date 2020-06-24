include:
  - .install
  - .start

salt_master_config_updated:
  file.managed:
    - name: /etc/salt/master
    - source: salt://components/misc_pkgs/saltstack/salt_master/files/master
    # - template: jinja
    - require:
      - install_salt_master
    - onchanges_in:
      - salt_master_service_restarted
