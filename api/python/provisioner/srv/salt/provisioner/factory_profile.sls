# TODO IMPROVE CORTX-8473 move to pillar to make configurable
{% set srv_factory_dir = '/var/lib/seagate/cortx/provisioner/shared/factory_profile' %}

factory_profile_copied:
  file.recurse:
    - name: {{ srv_factory_dir }}
    - source: salt://profile
    - file_mode: keep
    - clean: True
    - keep_source: True
