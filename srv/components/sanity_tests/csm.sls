{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Run CSM sanity tests:
  cmd.run:
    - name: csm_test -f /opt/seagate/eos/csm/test/test_data/args.yaml -t /opt/seagate/eos/csm/test/plans/self_test.pln 
2>&1 | tee -a {{ logfile }}
    - require:
      - Run S3 Sanity tests


{% endif %}