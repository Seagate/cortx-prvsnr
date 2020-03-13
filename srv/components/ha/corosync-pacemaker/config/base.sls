#Configurations for Corosync and Pacemaker Setup

Enable corosync service:
  service.enabled:
    - name: corosync

Enable pacemaker service:
  service.enabled:
    - name: pacemaker

Start pcsd service:
  service.running:
    - name: pcsd
    - enable: True

Create ha user:
  user.present:
    - name: {{ pillar['corosync-pacemaker']['user'] }}
    - password: {{ pillar['corosync-pacemaker']['password'] }}
    - uid: 189
    - gid: 189
    - groups:
      - haclient
    - allow_uid_change: True
    - allow_gid_change: True
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Authorize nodes:
  pcs.auth:
    - name: pcs_auth__auth
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ pillar['cluster'][node_id]['hostname'] }}
      {%- endfor %}
    - pcsuser: {{ pillar['corosync-pacemaker']['user'] }}
    - pcspasswd: {{ pillar['corosync-pacemaker']['password'] }}
    - extra_args:
      - '--force'
    - require:
      - Start pcsd service
{% endif %}