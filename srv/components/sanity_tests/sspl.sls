{% if grains['is_primary'] -%}
{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}
Create SSPL Sanity test script:
  file.managed:
      - name: /tmp/sspl-sanity.sh
      - create: True
      - makedirs: True
      - replace: True
      - user: root
      - group: root
      - mode: 755
      - contents: |
          #!/bin/bash
          echo "Runnign SSPL sanity"
          echo "state=active" > /var/eos/sspl/data/state.txt
          PID=$(/sbin/pidof -s /usr/bin/sspl_ll_d)
            kill -s SIGHUP $PID
          sh /opt/seagate/eos/sspl/sspl_test/run_tests.sh

Run SSPL Sanity tests:
  cmd.run:
    - name: bash /tmp/sspl-sanity.sh 2>&1 | tee {{ logfile }}
    - require:
      - Create SSPL Sanity test script

Housekeeping:
  file.absent:
    - name: /tmp/sspl-sanity.sh
    - require:
      - Run SSPL Sanity tests

{% endif %}
