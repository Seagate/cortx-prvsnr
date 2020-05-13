{% import_yaml 'components/defaults.yaml' as defaults %}

include:
  - components.ha.cortx-ha.ha_cleanup

Reset cortx-ha reset:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:reset')

Remove cortx-ha:
  pkg.purged:
    - name: cortx-ha

Delete cortx-ha yum repo:
  pkgrepo.absent:
    - name: {{ defaults.cortx_ha.repo.id }}

Delete cortx-ha checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.cortx-ha
