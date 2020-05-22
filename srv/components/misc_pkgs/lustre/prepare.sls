{% set lustre_repo = pillar['lustre']['repo'] %}
{% if salt['cmd.run']('lspci -d"15b3:1017:0200"') %}
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
