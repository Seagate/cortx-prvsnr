{% import_yaml 'components/defaults.yaml' as defaults %}

Add EOSCore yum repo:
  pkgrepo.managed:
    - name: {{ defaults.eoscore.repo.id }}
    - enabled: True
    - humanname: eoscore
    - baseurl: {{ defaults.eoscore.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.eoscore.repo.gpgkey }}
