setup_system_packages:
  pkg.installed:
    - pkgs:
      - iproute
  cmd.rum: "rm -rf /var/cache/yum"