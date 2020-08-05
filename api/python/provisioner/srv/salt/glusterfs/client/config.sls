{% for server, volume, mount_dir in salt['pillar.get']('glusterfs_mounts', []) %}

# TODO IMPROVE CORTX-9581 there is a possible issue with fstab, SaltStack #39757

glusterfs_volume_{{ volume }}_mounted:
  mount.mounted:
    - name: {{ mount_dir }}
    - device: {{ server }}:{{ volume }}
    - mkmnt: True
    - fstype: glusterfs
    - opts: _netdev,defaults,acl
    - persist: True
    - dump: 0
    - pass_num: 0

{% endfor %}
