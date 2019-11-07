#Configurations for Corosync and Pacemaker Setup

#Disable SELINUX policy
#  cmd.run:
#    - name: sed -i "s/SELINUX=.*/SELINUX=disable/g" /etc/selinux/config
#

Disable firewall:
  service.dead:
    - name: firewalld
    - enable: False 

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
    - password: {{ pillar['corosync-pacemaker']['password'] }}               # To be set using 'openssl passwd -1'
    - hash_password: True
    - createhome: True
    
{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Authorize nodes:
  pcs.auth:
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ pillar['cluster'][node_id]['fqdn'] }}
      {%- endfor %}
    - pcsuser: {{ pillar['corosync-pacemaker']['user'] }}
    - pcspasswd: {{ pillar['corosync-pacemaker']['password'] }}
    - extra_args:
      - '--force'
    - require:
      - user: Create ha user
 
Setup Cluster:
  pcs.cluster_setup:
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ pillar['cluster'][node_id]['fqdn'] }}
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

Disable STONITH:
  pcs.prop_has_value:
    - prop: stonith-enabled
    - value: false

{% endif %}
