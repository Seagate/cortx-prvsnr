{% import_yaml 'components/defaults.yaml' as defaults %}

Add Lustre yum repo:
  pkgrepo.managed:
    - name: {{ defaults.lustre.repo.id }}
    - enabled: True
    - humanname: lustre
{% if salt['cmd.run']('lspci -d"15b3:*"') %}
    - baseurl: {{ defaults.lustre.repo.url.o2ib }}
{% else %}
    - baseurl: {{ defaults.lustre.repo.url.tcp }}
{% endif %}
    - gpgcheck: 0
