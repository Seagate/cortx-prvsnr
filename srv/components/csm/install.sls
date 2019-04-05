{% import_yaml 'components/defaults.yaml' as defaults %}

include:
  - components.sspl

add_graphana_repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.grafana_repo.id }}
    - enabled: True
    - baseurl: {{ defaults.csm.grafana_repo.url }}
    - gpgcheck: 0

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

add_csm_repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.repo.id }}
    - enabled: True
    - baseurl: {{ defaults.csm.repo.url }}
    - gpgcheck: 0

install_csm:
  pkg.installed:
    - name: {{ defaults.csm.repo.package.name }}
    - version: {{ defaults.csm.repo.package.version }}
    - refresh: True
    - require:
      - pkgrepo: add_csm_repo

{% else %}

install_statsd:
  pkg.installed:
    - pkgs:
      - statsd
      - python2-statsd
    - refresh: True
