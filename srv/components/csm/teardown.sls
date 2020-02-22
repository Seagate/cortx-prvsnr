{% import_yaml 'components/defaults.yaml' as defaults %}

include:
  - components.csm.stop

Remove csm package:
  pkg.purged:
    - pkgs:
      - eos-csm_agent
      - eos-csm_web

Remove CSM configs:
  file.absent:
    - name: /etc/csm

Delete CSM yum repo:
  pkgrepo.absent:
    - name: {{ defaults.csm.repo.id }}

Remove stats collector:
  file.absent:
    - name: /opt/statsd/csm-stats-collector

Remove Symlink:
  file.absent:
    - name: /usr/bin/csm-stats-collector
    
Remove crontab:
  cron.absent:
    - name: /opt/statsd/csm-stats-collector 10
    - user: root
    - identifier: csm-stats-collector

Remove statsd utils:
  pkg.purged:
    - name: stats-utils

Delete csm checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.csm
