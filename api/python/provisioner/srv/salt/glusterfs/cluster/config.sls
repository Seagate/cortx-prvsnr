glusterfs_servers_peered:
  glusterfs.peered:
    - names:
{% for peer in salt['pillar.get']('glusterfs_peers', []) %}
      - {{ peer }}
{% endfor %}

# TODO IMPRVOVE ??? CORTX-9581 it might be necessary
#      to add some sleep / wait here since 'peer probe' might be async ???

{% for volume, bricks in salt['pillar.get']('glusterfs_volumes', {}).items() %}

glusterfs_volume_{{ volume }}_created:
  glusterfs.volume_present:
    - name: {{ volume }}
    - bricks:
  {% for server, path in bricks.items() %}
      - {{ server }}:{{ path }}
  {% endfor %}
    - replica: {{ bricks|length }}
    - start: True
    - force: True
    - require:
      - glusterfs_servers_peered

{% endfor %}
