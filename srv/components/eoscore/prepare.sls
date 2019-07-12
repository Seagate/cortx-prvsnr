{% import_yaml 'components/defaults.yaml' as defaults %}

Add Lustre yum repo:
  pkgrepo.managed:
    - name: {{ defaults.lustre.repo.id }}
    - enabled: True
    - humanname: lustre
    - baseurl: {{ defaults.lustre.repo.url }}
    - gpgcheck: 0

Add eoscore yum repo:
  pkgrepo.managed:
    - name: {{ defaults.eoscore.repo.id }}
    - enabled: True
    - humanname: eoscore
    - baseurl: {{ defaults.eoscore.repo.url }}
    - gpgcheck: 0
