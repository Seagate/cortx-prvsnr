{% import_yaml 'components/defaults.yaml' as defaults %}

Add uds yum repo:
  pkgrepo.managed:
    - name: {{ defaults.uds.repo.id }}
    - enabled: True
    - humanname: uds
    - baseurl: {{ defaults.uds.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.uds.repo.gpgkey }}

Create /var/csm directory:
  file.directory:
    - name: /var/csm
    - makedirs: True
    - mode: 700
    - user: csm
    - group: csm

Create /var/csm/tls directory:
  file.directory:
    - name: /var/csm/tls
    - makedirs: True
    - mode: 700
    - user: csm
    - group: csm
