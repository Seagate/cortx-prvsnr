# TODO IMPROVE CORTX-8473 salt version from pillar

# TODO IMPROVE CORTX-8473 is it needed ???
# Remove any older saltstack if any.
# systemctl stop salt-minion salt-master || true
# yum remove -y salt-minion salt-master


# TODO TEST CORTX-8473
saltstack_installed:
  pkg.installed:
    - pkgs:
      - salt-master
      - salt-minion
