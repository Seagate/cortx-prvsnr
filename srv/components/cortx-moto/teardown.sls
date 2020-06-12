{% import_yaml 'components/defaults.yaml' as defaults %}

Stage - Reset Core:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/core/conf/setup.yaml', 'core:reset')

Remove CortxMoto package:
  pkg.purged:
    - pkgs:
      - cortx-moto
      # - mero-debuginfo

Delete CortxMoto yum repo:
  pkgrepo.absent:
    - name: {{ defaults.cortx_moto.repo.id }}

Remove configuration file:
  file.absent:
    - names:
      - /etc/sysconfig/moto
      - /etc/sysconfig/moto.bak

Delete CortxMoto checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.cortx-moto
