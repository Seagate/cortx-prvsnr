include:
  - components.hare.prepare

Hare requisites:
  pkg.installed:
    - pkgs:
      - jq

Install hare:
  pkg.installed:
    - name: cortx-hare
    - version: latest
    - refresh: True
    - require:
      - pkg: Hare requisites
