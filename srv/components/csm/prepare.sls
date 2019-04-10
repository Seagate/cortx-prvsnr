{% import_yaml 'components/defaults.yaml' as defaults %}

add_graphana_repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.grafana_repo.id }}
    - enabled: True
    - baseurl: {{ defaults.csm.grafana_repo.url }}
    - gpgcheck: 0

add_csm_repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.repo.id }}
    - enabled: True
    - baseurl: {{ defaults.csm.repo.url }}
    - gpgcheck: 0
