{% if salt['cmd.run']('lspci -d"15b3:*"') %}
Install Mellanox card drivers:
  pkg.installed:
    - pkgs: 
      - mlnx-ofed-all
      - mlnx-fw-updater       # For EOS-4152
{% endif %}
