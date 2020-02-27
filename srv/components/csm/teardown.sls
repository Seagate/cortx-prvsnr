{% import_yaml 'components/defaults.yaml' as defaults %}
Stage - Reset CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:reset')

Remove statsd utils:
  pkg.purged:
    - name: stats_utils

Remove csm package:
  pkg.purged:
    - pkgs:
      - eos-csm_agent
      - eos-csm_web

Delete CSM yum repo:
  pkgrepo.absent:
    - name: {{ defaults.csm.repo.id }}

Delete csm checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.csm
