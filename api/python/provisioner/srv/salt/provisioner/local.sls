# TODO IMPROVE EOS-8473 move to pillar to make configurable
{% set install_dir = '/opt/seagate/eos-prvsnr' %}

repo_installed:
  file.recurse:
    - name: {{ install_dir }}
    - source: salt://provisioner/files/repo
    - keep_source: True
    - clean: True  # ???
