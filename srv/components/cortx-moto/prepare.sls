{% import_yaml 'components/defaults.yaml' as defaults %}

Add CortxMoto yum repo:
  pkgrepo.managed:
    - name: {{ defaults.cortx_moto.repo.id }}
    - enabled: True
    - humanname: cortx-moto
    - baseurl: {{ defaults.cortx_moto.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.cortx_moto.repo.gpgkey }}
