include:
  # Dependecies
  - components.misc_pkgs.consul
  - components.misc_pkgs.elasticsearch
  - components.misc_pkgs.kibana
  - components.misc_pkgs.statsd
  - components.misc_pkgs.nodejs
  # HA component
  - components.ha.corosync-pacemaker
  # - components.sspl
  - components.csm.prepare
  - components.csm.install
  - components.csm.config
  - components.csm.start
  - components.csm.housekeeping
  - components.csm.sanity_check
