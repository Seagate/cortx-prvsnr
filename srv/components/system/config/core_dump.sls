Relocate core dump to /var/crash:
  sysctl.present:
    - name: kernel.core_pattern
    - value: /var/crash/core-%e.%p
    - config: /etc/sysctl.d/200-motr-dumps.conf

Load updated sysctl settings:
  cmd.run:
    - name: sysctl -p /etc/sysctl.d/200-motr-dumps.conf
    - require:
      - Relocate core dump to /var/crash