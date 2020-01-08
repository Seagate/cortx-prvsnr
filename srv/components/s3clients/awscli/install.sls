Install python packages:
  pkg.installed:
    - pkgs:
      - vim-enhanced
      - jq
      - python2-pip
      - python3
      - python3-pip
    - reload_modules: true

Install AWS CLI:
  pip.installed:
    - name: awscli
    - upgrade: True
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: '/usr/bin/pip3'
    - require:
      - pkg: Install python packages

Install awscli-plugin-endpoint:
  pip.installed:
    - name: awscli-plugin-endpoint
    - upgrade: True
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: '/usr/bin/pip3'
    - require:
      - pkg: Install python packages
