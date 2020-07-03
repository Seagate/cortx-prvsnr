{% for _dir in salt['pillar.get']('glusterfs_dirs', []) %}

gluster_brick_directory_{{ _dir }}_exists:
  file.directory:
    - name: {{ _dir }}
    - makedirs: true

{% endfor %}
