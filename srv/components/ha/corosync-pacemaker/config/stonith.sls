{% if pillar['cluster'][grains['id']]['is_primary'] -%}

Remove stonith id stonith-c1 if already present:
  cmd.run:
    - name: pcs stonith delete stonith-c1
    - onlyif: pcs stonith show stonith-c1

Remove stonith id stonith-c2 if already present:
  cmd.run:
    - name: pcs stonith delete stonith-c2
    - onlyif: pcs stonith show stonith-c2

Prepare for stonith on node-1:
  cmd.run:
    - name: pcs stonith create stonith-c1 fence_ipmilan ipaddr={{ pillar['cluster']['srvnode-1']['bmc']['ip'] }} login={{ pillar['cluster']['srvnode-1']['bmc']['user'] }} passwd={{ salt['lyveutil.decrypt']('cluster', pillar['cluster']['srvnode-1']['bmc']['secret']) }} delay=5 pcmk_host_list=srvnode-1 pcmk_host_check=static-list lanplus=true auth=PASSWORD power_timeout=40 op monitor interval=10s 
    - unless: pcs stonith show stonith-c1

Prepare for stonith on node-2:
  cmd.run:
    - name: pcs stonith create stonith-c2 fence_ipmilan ipaddr={{ pillar['cluster']['srvnode-2']['bmc']['ip'] }} login={{ pillar['cluster']['srvnode-2']['bmc']['user'] }} passwd={{ salt['lyveutil.decrypt']('cluster', pillar['cluster']['srvnode-2']['bmc']['secret']) }} pcmk_host_list=srvnode-2 pcmk_host_check=static-list lanplus=true auth=PASSWORD power_timeout=40 op monitor interval=10s
    - unless: pcs stonith show stonith-c2

Apply stonith for node-1:
  cmd.run:
    - name: pcs constraint location stonith-c1 avoids srvnode-1=INFINITY

Apply stonith for node-2:
  cmd.run:
    - name: pcs constraint location stonith-c2 avoids srvnode-2=INFINITY

{% else %}
No STONITH application:
  test.show_notification:
    - text: "STONITH application applies only to primary node. There's no execution on secondary node"
{% endif %}
