{% if grains['is_primary'] -%}

{%- set node = grains['id'] -%}

Remove stonith id stonith-c1 if already present:
  cmd.run:
    - name: pcs stonith delete stonith-c1
    - onlyif: pcs stonith show stonith-c1

Remove stonith id stonith-c2 if already present:
  cmd.run:
    - name: pcs stonith delete stonith-c2
    - onlyif: pcs stonith show stonith-c2

{%- for host, ip in salt['mine.get'](node, 'bmc_ip').items() -%}

{%- if host == grains['id'] -%}
Prepare for stonith on node-1:
  cmd.run:
    - name: pcs stonith create stonith-c1 fence_ipmilan ipaddr={{ ip }} login={{ pillar['cluster'][host]['bmc']['user'] }} passwd={{ salt['lyveutil.decrypt'](pillar['cluster'][host]['bmc']['secret'], 'cluster') }} delay=5 pcmk_host_list=srvnode-1 pcmk_host_check=static-list power_timeout=40 op monitor interval=10s
    - unless: pcs stonith show stonith-c1

{% else %}
Prepare for stonith on node-2:
  cmd.run:
    - name: pcs stonith create stonith-c2 fence_ipmilan ipaddr={{ ip }} login={{ pillar['cluster'][host]['bmc']['user'] }} passwd={{ salt['lyveutil.decrypt'](pillar['cluster'][host]['bmc']['secret'], 'cluster') }} pcmk_host_list=srvnode-2 pcmk_host_check=static-list power_timeout=40 op monitor interval=10s
    - unless: pcs stonith show stonith-c2

{% endif %}
{%- endfor -%}

Apply stonith for node-1:
  cmd.run:
    - name: pcs constraint location stonith-c1 avoids srvnode-1=INFINITY

Apply stonith for node-2:
  cmd.run:
    - name: pcs constraint location stonith-c2 avoids srvnode-2=INFINITY

{% endif %}
