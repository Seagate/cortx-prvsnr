{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
# Start Hare:
#   cmd.run:
#     - name: hctl bootstrap --conf-dir /var/lib/hare
{% endif %}