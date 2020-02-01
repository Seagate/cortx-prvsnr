include:
  - components.csm.stop

Remove csm package:
  pkg.purged:
    - pkgs:
      - eos_csm: latest

Remove CSM config:
  file.absent:
    - /etc/csm/cluster.conf

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

Delete csm configs:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.csm
