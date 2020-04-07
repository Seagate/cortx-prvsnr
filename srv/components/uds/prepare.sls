{% import_yaml 'components/defaults.yaml' as defaults %}

Add uds yum repo:
  pkgrepo.managed:
    - name: {{ defaults.uds.repo.id }}
    - enabled: True
    - humanname: uds
    - baseurl: {{ defaults.uds.repo.url }}
    - gpgcheck: 0
