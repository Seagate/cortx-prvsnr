{% import_yaml 'components/defaults.yaml' as defaults %}
include:
  - components.misc_pkgs.lustre.start

Remove Lustre:
  pkg.purged:
    - pkgs:
      - kmod-lustre-client
      - lustre-client

Delete Lnet config file:
  file.absent:
    - name: /etc/modprobe.d/lnet.conf

Delete Lustre yum repo:
  pkgrepo.absent:
    - name: {{ defaults.lustre.repo.id }}

Remove lustre checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.lustre
