{% import_yaml 'components/defaults.yaml' as defaults %}

Stage - Reset Core:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/core/conf/setup.yaml', 'core:reset')

Remove EOSCore package:
  pkg.purged:
    - pkgs:
      - mero
      # - mero-debuginfo

Delete EOSCore yum repo:
  pkgrepo.absent:
    - name: {{ defaults.eoscore.repo.id }}

include:
  - components.misc_pkgs.lustre.teardown