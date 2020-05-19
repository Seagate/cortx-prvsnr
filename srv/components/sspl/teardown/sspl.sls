Stage - Reset SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:reset')

{% import_yaml 'components/defaults.yaml' as defaults %}
Remove sspl packages:
  pkg.purged:
    - pkgs:
      - eos-sspl
      - eos-sspl-test

Remove flask:
  pip.removed:
    - name: flask

Delete sspl yum repo:
  pkgrepo.absent:
    - name: {{ defaults.sspl.repo.id }}

Delete sspl_prereqs yum repo:
  pkgrepo.absent:
    - name: {{ defaults.sspl.uploads_repo.id }}

Remove /opt/seagate/sspl configurations:
  file.absent:
    - names: 
      - /opt/seagate/sspl
      - /etc/sspl

Delete sspl checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.sspl
