{% if salt['cmd.run']('lspci -d"15b3:*"') %}
Install Lustre:
  pkg.installed:
    - fromrepo: lustre
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
