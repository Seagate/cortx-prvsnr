include:
  - components.misc_pkgs.elasticsearch
  - components.misc_pkgs.statsd


#CSM Configuration and Initialization
Initialize CSM setup:
  cmd.run:
    - name: csm_setup init -f
