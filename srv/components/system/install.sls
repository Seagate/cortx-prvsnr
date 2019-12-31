# update_yum_repos:
#   module.run:
#     - pkg.update:

Install_base_packages:
  pkg.installed:
    - pkgs:
      - ipmitool
      - python3
    - reload_modules: True

Install policy packages for SELinux:
  pkg.installed:
    - pkgs:
      - policycoreutils
      - policycoreutils-python

# Install python-pip packages (version 2 and 3)
# version 2 is needed for salt-minion's pip_state
python-pip:
  pkg.installed:
    - pkgs:
      - python3-pip
    - reload_modules: True
    - bin_env: /usr/bin/pip
    - upgrade: True
   
# Install pyyaml:
#   # Install using pip
#   pip.installed:
#     # The pip module we want to install
#     - name: pyyaml
#     # Absolute path to a virtual environment directory or absolute path to a pip executable
#     # We want to install python3 paramiko so we use pip3 here
#     - bin_env: '/usr/bin/pip3'
#     - upgrade: True
#     # Require python-pip state to be run before this one
#     - require:
#       - pkg: python-pip
