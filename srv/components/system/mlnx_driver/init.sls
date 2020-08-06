{% if salt['cmd.run']('lspci -d"15b3:1017:0200"') %}
Install Mellanox card drivers:
  pkg.installed:
    - pkgs:
      - mlnx-ofed-all
      - mlnx-fw-updater       # For CORTX-4152
{% endif %}
