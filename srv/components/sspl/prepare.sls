{% import_yaml 'components/defaults.yaml' as defaults %}

Add sspl_prereqs yum repo:
  pkgrepo.managed:
    - name: {{ defaults.sspl.uploads_repo.id }}
    - enabled: True
    - humanname: sspl_uploads
    - baseurl: {{ defaults.sspl.uploads_repo.url }}
    - gpgcheck: 0

Add sspl yum repo:
  pkgrepo.managed:
    - name: {{ defaults.sspl.repo.id }}
    - enabled: True
    - humanname: sspl
    - baseurl: {{ defaults.sspl.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.sspl.repo.gpgkey }}
