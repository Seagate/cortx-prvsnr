include:
  - components.ha.corosync-pacemaker.install

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
    - require:
      - Install corosync

Enable pacemaker service:
  service.dead:
    - name: pacemaker
    - enable: True
    - require:
      - Install pacemaker

Start pcsd service:
  service.running:
    - name: pcsd
    - enable: True
    - require:
      - Install pcs

{% if 'primary' in grains['roles'] %}
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
{% endif %}