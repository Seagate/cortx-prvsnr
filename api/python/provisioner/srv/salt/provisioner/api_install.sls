prvsnrusers:
  group.present

# TODO IMPROVE EOS-8473 consider states instead
user_salt_roots_created:
  cmd.script:
    - source: salt://provisioner/files/api.sh

api_installed:
  pip.installed:
    - name: /opt/seagate/eos-prvsnr/api/python
    - bin_env: /usr/bin/pip3
    - upgrade: True
