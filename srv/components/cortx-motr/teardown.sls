{% import_yaml 'components/defaults.yaml' as defaults %}

Stage - Reset Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'motr:reset')

Remove CortxMotr package:
  pkg.purged:
    - pkgs:
      - cortx-motr
      # - mero-debuginfo

Delete CortxMotr yum repo:
  pkgrepo.absent:
    - name: {{ defaults.cortx_motr.repo.id }}

Remove configuration file:
  file.absent:
    - names:
      - /etc/sysconfig/motr
      - /etc/sysconfig/motr.bak

Delete CortxMotr checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.cortx-motr
