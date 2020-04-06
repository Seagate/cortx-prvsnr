Install_base_packages:
  pkg.installed:
    - pkgs:
      - sudo
      - ipmitool
      - python3
    - reload_modules: True

Install policy packages for SELinux:
  pkg.installed:
    - pkgs:
      - policycoreutils
      - policycoreutils-python

# Install python-pip packages (version 2 and 3)
python-pip:
  pkg.installed:
    - pkgs:
      - python3-pip
    - reload_modules: True
    - bin_env: /usr/bin/pip
    - upgrade: True

Install cryptography python package:
  pip.installed:
    - name: cryptography
    - bin_env: /usr/bin/pip3
    - target: /usr/lib64/python3.6/site-packages/

Install eos-py-utils:           # Package for cryptography
  pkg.installed:
    - name: eos-py-utils
    - requrie:
      - Install cryptography python package
