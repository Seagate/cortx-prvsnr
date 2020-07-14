{% import_yaml 'components/defaults.yaml' as defaults %}

Add Motr yum repo:
  pkgrepo.managed:
    - name: {{ defaults.motr.repo.id }}
    - enabled: True
    - humanname: motr
    - baseurl: {{ defaults.motr.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.motr.repo.gpgkey }}
