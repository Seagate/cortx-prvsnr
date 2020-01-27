# start corosync-pacemaker through pcs
{% if pillar['cluster'][grains['id']]['is_primary'] -%}
start corosync-pacemaker:
  cmd.run:
    - name: pcs cluster start --all
{% endif %}

