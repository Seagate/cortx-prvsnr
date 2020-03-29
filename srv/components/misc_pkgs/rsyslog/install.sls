Install rsyslog service:
  pkg.installed:
    - name: rsyslog
    - version: {{ pillar ['commons']['version']['rsyslog'] }}
    - refresh: True

Install rsyslog extras:
  pkg.installed:
    - pkgs:
      - rsyslog-elasticsearch: {{ pillar ['commons']['version']['rsyslog-elasticsearch'] }}
      - rsyslog-mmjsonparse: {{ pillar ['commons']['version']['rsyslog-mmjsonparse'] }}
