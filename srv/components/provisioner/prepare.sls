{% import_yaml 'components/defaults.yaml' as defaults %}
Add provisioner yum repo:
  pkgrepo.managed:
    - name: {{ defaults.provisioner.repo.id }}
    - enabled: True
    - humanname: provisioner
    - baseurl: {{ defaults.provisioner.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.provisioner.repo.gpgkey }}
