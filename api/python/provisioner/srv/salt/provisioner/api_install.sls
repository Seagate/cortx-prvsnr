m2crypto_precompiled_installed:
  pkg.installed:
    - pkgs:
      - python36-m2crypto

api_installed:
  pip.installed:
    - name: /opt/seagate/cortx/provisioner/api/python
    - bin_env: /usr/bin/pip3
    - upgrade: False  # to reuse already installed dependencies
                      # that may come from rpm repositories

prvsnrusers:
  group.present


# TODO IMPROVE EOS-8473 consider states instead
api_post_setup_applied:
  cmd.script:
    - source: salt://provisioner/files/post_setup.sh

salt_dynamic_modules_synced:
  cmd.run:
    # TODO IMPROVE EOS-9581: cmd.run is a workaround since
    # as a module.run it doens't work as expected
    # https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.saltutil.html
    - name: 'salt-call saltutil.sync_all'
    - onchanges:
      - api_installed
