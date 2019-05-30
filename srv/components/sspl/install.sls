{% if 'virtual' in salt['grains.get']('productname').lower() %}

Install prereq packages for sspl - vm specific:
  pkg.installed:
    - pkgs:
      - lxqt-policykit

{% else %}

Install prereq packages for sspl - hw specific:
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

{% endif %}

Install sspl packages:
  pkg.installed:
    - pkgs:
      - libsspl_sec
      - libsspl_sec-method_none
      - sspl
    - refresh: True
