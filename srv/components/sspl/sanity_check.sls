pip upgrade:
 pip.installed:
   - name: pip
   - bin_env: /bin/pip
   - upgrade: True

Install test prerequisites:
  pip.installed:
    - pkgs:
      - lettuce == 0.2.23
      - Flask == 1.1.1
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: /usr/bin/pip

Install sspl test:
  pkg.installed:
    - name: sspl-test

Run sspl test:
  cmd.run:
    - name: /opt/seagate/sspl/test/run_qa_test.sh
    - only_if: test -f /opt/seagate/sspl/test/run_qa_test.sh

# Clean-up 
Remove flask:
  pip.removed:
    - name: Flask
    - bin_env: /usr/bin/pip

Remove lettuce:
  pip.removed:
    - name: lettuce
    - bin_env: /usr/bin/pip
    