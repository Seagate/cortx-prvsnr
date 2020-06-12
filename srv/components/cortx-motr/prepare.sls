{% import_yaml 'components/defaults.yaml' as defaults %}

Add CortxMotr yum repo:
  pkgrepo.managed:
    - name: {{ defaults.cortx_motr.repo.id }}
    - enabled: True
    - humanname: cortx-motr
    - baseurl: {{ defaults.cortx_motr.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.cortx_motr.repo.gpgkey }}
