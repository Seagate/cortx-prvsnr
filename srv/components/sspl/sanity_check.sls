Install test prerequisites:
  pip.installed:
    - name: lettuce >= 0.2.23

Install sspl test:
  pkg.installed:
    - name: sspl-test

Run sspl test:
  cmd.run:
    - name: /opt/seagate/sspl/test/run_tests.sh
    - only_if: test -f /opt/seagate/sspl/test/run_tests.sh
