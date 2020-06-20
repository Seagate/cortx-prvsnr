include:
  - components.misc_pkgs.saltstack.prepare

install_salt_master:
  pkg.installed:
    - name: salt-master
