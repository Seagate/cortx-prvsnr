{% import_yaml 'components/defaults.yaml' as defaults %}

{% if salt['cmd.retcode']('lspci | grep "Ethernet controller: Mellanox Technologies MT27800 Family"') %}
Add Lustre yum repo:
  pkgrepo.managed:
    - name: {{ defaults.commons.repo.id }}
    - enabled: True
    - humanname: lustre
    - baseurl: {{ defaults.commons.repo.url }}
    - gpgcheck: 0
{% else %}
Add Lustre yum repo:
  pkgrepo.managed:
    - name: {{ defaults.lustre.repo.id }}
    - enabled: True
    - humanname: lustre
    - baseurl: {{ defaults.lustre.repo.url }}
    - gpgcheck: 0
{% endif %}