include:
  - components.misc_pkgs.saltstack.prepare

Install Salt Minion:
  pkg.installed:
    - name: salt-minion
    - order: last