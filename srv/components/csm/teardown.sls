include:
  - components.ha.corosync-pacemaker.teardown

Remove csm package:
  pkg.purged:
    - pkgs:
      - eos-csm
      - csm


