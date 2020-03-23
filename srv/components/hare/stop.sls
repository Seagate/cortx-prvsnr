{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
# Shutdown Cluster:
#   cmd.run:
#     - name: hctl shutdown
{% endif %}
