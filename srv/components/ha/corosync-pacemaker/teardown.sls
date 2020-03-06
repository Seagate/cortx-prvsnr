{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Destroy resource ClusterIP:
  cmd.run:
    - name: pcs resource delete ClusterIP
    - onlyif: pcs resource show ClusterIP

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
