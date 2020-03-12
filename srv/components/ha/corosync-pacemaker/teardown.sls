{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Destroy resource ClusterIP:
  cmd.run:
    - name: pcs resource delete ClusterIP
    - onlyif: pcs resource show ClusterIP

Clear Auth-tokens:
  cmd.run:
    - name: pcs pcsd clear-auth

Destroy Cluster:
  cmd.run:
    - name: pcs cluster destroy
{% endif %}

Remove user and group:
  user.absent:
    - name: hacluster
    - purge: True
    - force: True

{% for serv in ["corosync", "pacemaker", "pcsd"] %}
Stop service {{ serv }}:
  service.dead:
    - name: {{ serv }}
    - enable: False
{% endfor %}

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
