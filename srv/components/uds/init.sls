Install UDS:
  pkg.installed:
    - name: uds-pyi
    - version: {{ pillar['uds']['version']['uds-pyi'] }}
    - refresh: True
