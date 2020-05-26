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
    - pcspasswd: {{ salt['lyveutil.decrypt'](pillar['corosync-pacemaker']['secret'],'corosync-pacemaker') }}
    - extra_args:
      - '--force'
    - require:
      - Start pcsd service

 Setup Cluster:
   pcs.cluster_setup:
     - nodes:
       {%- for node_id in pillar['cluster']['node_list'] %}
       - {{ node_id }}
       {%- endfor %}
     - pcsclustername: {{ pillar['corosync-pacemaker']['cluster_name'] }}
     - extra_args:
       - '--start'
       - '--enable'
       - '--force'

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

{%- endif -%}
