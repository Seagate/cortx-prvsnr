Install test prerequisites:
  pip.installed:
    - name: lettuce >= 0.2.23
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: '/usr/bin/pip3'

Install sspl test:
  pkg.installed:
    - name: sspl-test

Run sspl test:
  cmd.run:
    - name: /opt/seagate/sspl/test/run_tests.sh
    - only_if: test -f /opt/seagate/sspl/test/run_tests.sh
