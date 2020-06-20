include:
  - components.misc_pkgs.saltstack.prepare

install_salt_minion:
  pkg.installed:
    - name: salt-minion
