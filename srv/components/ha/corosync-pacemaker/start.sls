# start corosync-pacemaker through pcs
{% if grains['is_primary'] -%}
start corosync-pacemaker:
  cmd.run:
    - name: pcs cluster start --all
{% endif %}
