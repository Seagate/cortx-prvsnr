Hare requisites:
  pkg.installed:
    - pkgs:
      - jq

Install hare:
  pkg.installed:
    - name: hare
    - version: latest
    - refresh: True
    - require:
      - pkg: Hare requisites
