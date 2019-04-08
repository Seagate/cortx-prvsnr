{% import_yaml 'components/defaults.yaml' as defaults %}

add_halon_repo:
  pkgrepo.managed:
    - name: {{ defaults.halon.repo.id }}
    - enabled: True
    - humanname: halon
    - baseurl: {{ defaults.halon.repo.url }}
    - gpgcheck: 0
