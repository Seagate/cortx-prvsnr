Remove uds package:
  pkg.purged:
    - name: uds

Delete uds yum repo:
  pkgrepo.absent:
    - name: {{ defaults.uds.repo.id }}
