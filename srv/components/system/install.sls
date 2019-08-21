# update_yum_repos:
#   module.run:
#     - pkg.update:

Install_base_packages:
  pkg.installed:
    - pkgs:
      - vim-enhanced
      - jq
      - python36
    # - tmux
    - reload_modules: True

# Install python-pip packages (version 2 and 3)
# version 2 is needed for salt-minion's pip_state
python-pip:
  pkg.installed:
    - pkgs:
      - python2-pip
      - python36-pip
    - reload_modules: True

pip3 upgrade:
  pip.installed:
    - name: pip
    - bin_env: /usr/bin/pip
    - upgrade: True
    - require:
      - pkg: python-pip


Install pyyaml:
  # Install using pip
  pip.installed:
    # The pip module we want to install
    - name: pyyaml
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: '/usr/bin/pip3'
    - upgrade: True
    # Require python-pip state to be run before this one
    - require:
      - pkg: python-pip
