{% import_yaml 'components/defaults.yaml' as defaults %}

include:
  - components.mero

add_halon_repo:
  pkgrepo.managed:
    - name: {{ defaults.halon.repo.id }}
    - enabled: True
    - humanname: halon
    - baseurl: {{ defaults.halon.repo.url }}
    - gpgcheck: 0

install_halon:
  pkg.installed:
    - pkgs:
      - halon
    - refresh: True
    - require:
      - pkgrepo: add_halon_repo
