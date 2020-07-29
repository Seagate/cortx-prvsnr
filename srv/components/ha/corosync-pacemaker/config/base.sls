# HA user has to be updated for setting new password.
# This has to happen only after pacemaker is installed.
Update ha user:
  user.present:
    - name: {{ pillar['corosync-pacemaker']['user'] }}
    - password: {{ salt['lyveutil.decrypt']('corosync-pacemaker', pillar['corosync-pacemaker']['secret']) }}
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

#Configurations for Corosync and Pacemaker Setup
Add hacluster user to haclient group:
  group.present:
    - name: haclient
    - addusers:
      - {{ pillar['corosync-pacemaker']['user'] }}

Enable corosync service:
  service.dead:
    - name: corosync
    - enable: True

Enable pacemaker service:
  service.dead:
    - name: pacemaker
    - enable: True

Start pcsd service:
  service.running:
    - name: pcsd
    - enable: True

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Authorize nodes:
  pcs.auth:
    - name: pcs_auth__auth
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ node_id }}
      {%- endfor %}
    - pcsuser: {{ pillar['corosync-pacemaker']['user'] }}
    - pcspasswd: {{ salt['lyveutil.decrypt']('corosync-pacemaker', pillar['corosync-pacemaker']['secret']) }}
    - extra_args:
      - '--force'
    - require:
      - Start pcsd service

Ignore the Quorum Policy:
  pcs.prop_has_value:
    - prop: no-quorum-policy
    - value: ignore

Enable STONITH:
  pcs.prop_has_value:
    - prop: stonith-enabled
{% if pillar['cluster'][grains['id']]['bmc']['ip'] %}
    - value: true
{% else %}
    - value: false
{% endif %}
{% else %}
No Cluster Setup:
  test.show_notification:
    - text: "Cluster setup applies only to primary node. There's no Cluster setup operation on secondary node"
{%- endif -%}
