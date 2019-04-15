{% import_yaml 'components/defaults.yaml' as defaults %}

add_sspl_prereqs_repo:
  pkgrepo.managed:
    - name: {{ defaults.sspl.uploads_repo.id }}
    - enabled: True
    - humanname: sspl_uploads
    - baseurl: {{ defaults.sspl.uploads_repo.url }}
    - gpgcheck: 0
    
add_sspl_repo:
  pkgrepo.managed:
    - name: {{ defaults.sspl.repo.id }}
    - enabled: True
    - humanname: sspl
    - baseurl: {{ defaults.sspl.repo.url }}
    - gpgcheck: 0
