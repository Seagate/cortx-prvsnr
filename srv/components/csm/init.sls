include:
  # Dependecies
  - components.misc.consul
  - components.misc.elasticsearch
  - components.misc.kibana
  - components.misc.statsd
  - components.misc.nodejs
  # HA component
  - components.ha.corosync-pacemaker
  # - components.sspl
  - components.csm.prepare
  - components.csm.install
  - components.csm.config
  - components.csm.start
  - components.csm.housekeeping
  - components.csm.sanity_check
