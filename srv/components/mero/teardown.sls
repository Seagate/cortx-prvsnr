{% import_yaml 'components/defaults.yaml' as defaults %}

delete_lnet_config:
  file.absent:
    - name: /etc/modprobe.d/lnet.conf

remove_mero:
  pkg.purged:
    - pkgs:
      - mero
      # - mero-debuginfo

Remove user mero:
  user.absent:
    - name: mero
    - purge: True
    - force: True

remove_lustre:
  pkg.purged:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel

del_lustre_repo:
  pkgrepo.absent:
    - name: {{ defaults.lustre.repo.id }}

del_mero_repo:
  pkgrepo.absent:
    - name: {{ defaults.mero.repo.id }}
