{% import_yaml '/opt/seagate/cortx/ha/conf/setup.yaml' as ha %}

Sync Files across nodes:
  cmd.run:
    name: |
      {% for file_name in ha.hare.backup.files %}
      {% for node in (pillar['cluster']['node_list'] | difference(grains['id'])) %}
      rsync -zavhe ssh file node:file
      {% endfor %}
      {% endfor %}
