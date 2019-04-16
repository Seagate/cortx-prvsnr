{% import_yaml 'components/defaults.yaml' as defaults %}

install_grafana:
  pkg.installed:
    - name: grafana
    - require:
      - pkgrepo: add_graphana_repo

install_graphite:
  pkg.installed:
    - pkgs:
      - graphite-web
      - python-carbon

install_csm:
  pkg.installed:
    - name: {{ defaults.csm.repo.package.name }}
    - version: {{ defaults.csm.repo.package.version }}
    - refresh: True

install_statsd:
  pkg.installed:
    - pkgs:
      - statsd
      - python2-statsd
    - refresh: True
