{% if pillar['cluster'][grains['id']]['is_primary'] -%}

Destroy Cluster:
  pcs.cluster_setup:
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
        - {{ pillar['cluster'][node_id]['hostname'] }}
      {%- endfor -%}
    - pcsclustername: {{ pillar['corosync-pacemaker']['cluster_name'] }}
    - extra_args:
      - '--stop'
      - '--destroy'

Stop Cluster:
  cmd.run:
    - name: pcs cluster stop --force

Destroy Cluster:
  cmd.run:
    - name: pcs cluster destroy

{%- endif -%}

Remove user and group:
  cmd.run:
    - names: 
      - userdel {{ pillar['corosync-pacemaker']['user'] }}

Remove pcs package:
  pkg.purged:
    - pkgs:
      - pcs
      - pacemaker
      - corosync

# Enable and Start Firewall:
#   cmd.run:
#     - names:
#       - systemctl enable firewalld
#       - systemctl start firewalld
