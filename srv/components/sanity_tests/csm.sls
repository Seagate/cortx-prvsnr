{% if pillar['cluster'][grains['id']]['is_primary'] -%}

{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}

Run CSM sanity tests:
  cmd.run:
    - name: /usr/bin/csm_test -f /opt/seagate/cortx/csm/test/test_data/args.yaml -t /opt/seagate/cortx/csm/test/plans/self_test.pln 2>&1 | tee -a {{ logfile }}

{% endif %}
