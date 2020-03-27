Install rsyslog service:
  pkg.installed:
    - name: rsyslog
    - version: {{ pillar ['commons']['version']['rsyslog'] }}
    - refresh: True
