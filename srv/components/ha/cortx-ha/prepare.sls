{% import_yaml 'components/defaults.yaml' as defaults %}

Add cortx-ha yum repo:
  pkgrepo.managed:
    - name: {{ defaults.cortx_ha.repo.id }}
    - enabled: True
    - humanname: cortx-ha
    - baseurl: {{ defaults.cortx_ha.repo.url }}
    - gpgcheck: 0
