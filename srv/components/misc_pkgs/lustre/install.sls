{% if salt['cmd.retcode']('lspci | grep "Ethernet controller: Mellanox Technologies MT27800 Family"') %}
Install Lustre:
  pkg.installed:
    - fromrepo: commons
    - pkgs:
      - kmod-lustre-client: latest
      - lustre-client: latest
    - refresh: True
{% else %}
Install Lustre:
  pkg.installed:
    - fromrepo: lustre
    - pkgs:
      - kmod-lustre-client: latest
      - lustre-client: latest
    - refresh: True
{% endif %}