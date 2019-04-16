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
