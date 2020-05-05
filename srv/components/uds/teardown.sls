{% import_yaml 'components/defaults.yaml' as defaults %}

Remove USL cert file:
  file.absent:
    - names:
      - /var/csm/tls

Remove uds package:
  pkg.purged:
    - name: uds

Delete uds yum repo:
  pkgrepo.absent:
    - name: {{ defaults.uds.repo.id }}
