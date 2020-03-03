{%- for node_id in pillar['cluster']['node_list'] %}
Remove authorized nodes:
  cmd.run:
    - name: pcs cluster node remove {{ pillar['cluster'][node_id]['hostname'] }}
{%- endfor %}

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Destroy Cluster:
  cmd.run:
    - name: pcs cluster destroy
{% endif %}

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

Remove configuration directory
  file.absent:
    - names:
      - /etc/corosync
      - /etc/pacemaker

Remove corosync-pacemaker data:
  file.absent:
    - names:
      - /var/lib/corosync
      - /var/lib/pacemaker
      - /var/lib/pcsd 

# Enable and Start Firewall:
#   cmd.run:
#     - names:
#       - systemctl enable firewalld
#       - systemctl start firewalld
