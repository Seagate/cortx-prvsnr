# update_yum_repos:
#   module.run:
#     - pkg.update:

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
# version 2 is needed for salt-minion's pip_state
python-pip:
  pkg.installed:
    - pkgs:
      - python3-pip
    - reload_modules: True
    - bin_env: /usr/bin/pip
    - upgrade: True
