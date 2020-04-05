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

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Authorize nodes:
  pcs.auth:
    - name: pcs_auth__auth
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ pillar['cluster'][node_id]['hostname'] }}
      {%- endfor %}
    - pcsuser: {{ pillar['corosync-pacemaker']['user'] }}
    - pcspasswd: {{ salt['lyveutil.decrypt'](pillar['corosync-pacemaker']['secret'],'corosync-pacemaker') }}
    - extra_args:
      - '--force'
    - require:
      - Start pcsd service
{% endif %}