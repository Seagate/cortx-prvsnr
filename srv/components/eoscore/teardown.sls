{% import_yaml 'components/defaults.yaml' as defaults %}

# Mostly we would have uninstalled halond already
# Without halond service, this wouldn't make sense
{% if salt['service.status']('halond.service') %}
Cleanup eoscore:
  service.running:
    - name: mero-cleanup
{% endif %}

Remove eoscore package:
  pkg.purged:
    - pkgs:
      - mero
      # - mero-debuginfo

Delete eoscore yum repo:
  pkgrepo.absent:
    - name: {{ defaults.eoscore.repo.id }}

Remove Lustre:
  pkg.purged:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel

Delete Lnet config file:
  file.absent:
    - name: /etc/modprobe.d/lnet.conf

Delete Lustre yum repo:
  pkgrepo.absent:
    - name: {{ defaults.lustre.repo.id }}
