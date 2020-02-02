{% import_yaml 'components/defaults.yaml' as defaults %}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
include:
  - components.hare.stop

Stage - Reset Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:reset')

Remove Hare:
 pkg.purged:
  - name: hare

Delete Hare yum repo:
  pkgrepo.absent:
    - name: {{ defaults.hare.repo.id }}
{% endif %}

Remove hare checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.hare
