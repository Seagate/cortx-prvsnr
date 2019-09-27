#Configurations for Corosync and Pacemaker Setup

#Disable SELINUX policy
#  cmd.run:
#    - name: sed -i "s/SELINUX=.*/SELINUX=disable/g" /etc/selinux/config
#

Disable firewall:
  cmd.run:
    - names: 
      - systemctl stop firewalld
      - systemctl disable firewalld

Create HA Client and Cluster:
  cmd.run:
    - names: 
      - getent group haclient >/dev/null || groupadd -r haclient -g 189
      - getent passwd hacluster >/dev/null || useradd -r -g haclient -u 189 -s /sbin/nologin -c "cluster user" {{ pillar['csm']['user'] }}

{% set node = grains['id'] %}
{% if pillar['cluster'][node]['is_primary'] %}

Configure password for user:
  cmd.run:
    - name: echo {{ pillar['csm']['password'] }} | passwd --stdin {{ pillar['csm']['user'] }}


Authorize nodes:
  cmd.run:
    - names:
      - pcs pcsd clear-auth --remote
      - service pcsd restart
      - pcs cluster auth -u {{ pillar['csm']['user'] }} -p {{ pillar['csm']['password'] }} {{ pillar["cluster"]["node_list"][0] }}


Setup Cluster:
  cmd.run:
    - name: pcs cluster setup --name {{ pillar['csm']['cluster_name'] }} {{ pillar["cluster"]["node_list"][0] }}

Start cluster services:
  cmd.run:
    - names:
      - pcs cluster start --all
      - pcs cluster enable --all

Disable STONITH and Ignore the Quorum Policy:
  cmd.run:
    - names:
      - pcs property set stonith-enabled=false
      - pcs property set no-quorum-policy=ignore

{% endif %}
