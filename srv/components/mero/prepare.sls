{% import_yaml 'components/defaults.yaml' as defaults %}

add_lustre_repo:
  pkgrepo.managed:
    - name: {{ defaults.lustre.repo.id }}
    - enabled: True
    - humanname: lustre
    - baseurl: {{ defaults.lustre.repo.url }}
    - gpgcheck: 0

add_mero_repo:
  pkgrepo.managed:
    - name: {{ defaults.mero.repo.id }}
    - enabled: True
    - humanname: mero
    - baseurl: {{ defaults.mero.repo.url }}
    - gpgcheck: 0
