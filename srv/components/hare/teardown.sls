{% import_yaml 'components/defaults.yaml' as defaults %}
{% if salt["grains.get"]('is_primary', false) %}
include:
  - components.hare.stop

Stage - Reset Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:reset')

Remove cluster yaml:
  file.absent:
    - name: /var/lib/hare
{% endif %}

Remove Hare:
  pkg.purged:
    - name: eos-hare

Remove jq:
  pkg.purged:
    - name: jq

Delete Hare yum repo:
  pkgrepo.absent:
    - name: {{ defaults.hare.repo.id }}

Remove hare checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.hare
