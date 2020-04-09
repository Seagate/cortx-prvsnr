Install runtime libraries:
  pkg.installed:
    - pkgs:
      - corosync
      - pacemaker
      - pcs
      - fence-agents-ipmilan    # For fencing
