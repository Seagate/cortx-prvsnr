setup_utils:
  pkg.installed:
    - pkgs:
      - git
      - unzip
  cmd.run: "rm -rf /var/cache/yum"
