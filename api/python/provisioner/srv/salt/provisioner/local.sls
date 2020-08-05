# TODO IMPROVE CORTX-8473 move to pillar to make configurable
{% set install_dir = '/opt/seagate/cortx/provisioner' %}

repo_installed:
  file.recurse:
    - name: {{ install_dir }}
    - source: salt://provisioner/files/repo
    - keep_source: True
    - clean: True  # ???
