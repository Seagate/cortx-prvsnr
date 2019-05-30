{% import_yaml 'components/defaults.yaml' as defaults %}

Remove mero package:
  pkg.purged:
    - pkgs:
      - mero
      # - mero-debuginfo

Delete Mero yum repo:
  pkgrepo.absent:
    - name: {{ defaults.mero.repo.id }}

Remove Lustre:
  pkg.purged:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel

Delete Lustre yum repo:
  pkgrepo.absent:
    - name: {{ defaults.lustre.repo.id }}


Delete Lnet config file:
  file.absent:
    - name: /etc/modprobe.d/lnet.conf
