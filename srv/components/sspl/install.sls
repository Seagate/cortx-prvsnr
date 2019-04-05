{% import_yaml 'components/defaults.yaml' as defaults %}

include:
  - components.system.install.base

add_sspl_prereqs_repo:
  pkgrepo.managed:
    - name: {{ defaults.sspl.uploads_repo.id }}
    - enabled: True
    - humanname: sspl_uploads
    - baseurl: {{ defaults.sspl.uploads_repo.url }}
    - gpgcheck: 0

{% if (not salt['grains.get']('productname').lower().startswith('virtual')) %}
install_sspl_prereqs_hw_pecific:
  pkg.installed:
    - pkgs:
      - sg3_utils
      - openhpi
      - gemhpi
      - pull_sea_logs
      - python-daemon
      - python-hpi
      - python-openhpi-baselib
      - zabbix-agent-lib
      - zabbix-api-gescheit
      - zabbix-xrtx-lib
      - zabbix-collector
    - refresh: True
    - require:
      - pkgrepo: add_sspl_prereqs_repo
{% else %}
install_sspl_prereqs_vm_pecific:
  pkg.installed:
    - pkgs:
      - lxqt-policykit
{% endif %}

add_sspl_repo:
  pkgrepo.managed:
    - name: {{ defaults.sspl.repo.id }}
    - enabled: True
    - humanname: sspl
    - baseurl: {{ defaults.sspl.repo.url }}
    - gpgcheck: 0

install_sspl:
  pkg.installed:
    - pkgs:
      - lxqt-policykit
      - libsspl_sec
      - libsspl_sec-method_none
      - sspl
    - refresh: True
    - require:
      - pkgrepo: add_sspl_repo
