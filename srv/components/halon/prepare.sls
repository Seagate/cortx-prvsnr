{% import_yaml 'components/defaults.yaml' as defaults %}

Add Halon yum repo:
  pkgrepo.managed:
    - name: {{ defaults.halon.repo.id }}
    - enabled: True
    - humanname: halon
    - baseurl: {{ defaults.halon.repo.url }}
    - gpgcheck: 0
