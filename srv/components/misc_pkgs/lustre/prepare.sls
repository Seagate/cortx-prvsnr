{% set lustre_repo = pillar['commons']['repo']['lustre'] %}
{% if salt['cmd.run']('lspci -d"15b3:*"|grep Mellanox') %}
Add Lustre yum repo:
  pkgrepo.managed:
    - name: lustre
    - enabled: True
    - humanname: lustre
    - baseurl: {{ lustre_repo }}/o2ib
    - gpgcheck: 0
{% else %}
Add Lustre yum repo:
  pkgrepo.managed:
    - name: lustre
    - enabled: True
    - humanname: lustre
    - baseurl: {{ lustre_repo }}/tcp
    - gpgcheck: 0
{% endif %}
