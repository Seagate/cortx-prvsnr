{% import_yaml 'components/defaults.yaml' as defaults %}

remove_grafana:
  pkg.purged:
    - name: grafana
    - require:
      - pkgrepo: add_graphana_repo

remove_graphite:
  pkg.purged:
    - pkgs:
      - graphite-web
      - python-carbon

remove_csm:
  pkg.purged:
    - name: {{ defaults.csm.repo.package.name }}
    - version: {{ defaults.csm.repo.package.version }}
    - refresh: True

remove_statsd:
  pkg.purged:
    - pkgs:
      - statsd
      - python2-statsd
    - refresh: True
