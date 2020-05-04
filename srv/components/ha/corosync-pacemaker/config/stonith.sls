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
    - name: pcs stonith create stonith-c1 fence_ipmilan ipaddr={{ pillar['cluster']['eosnode-1']['bmc']['ip'] }} login={{ pillar['cluster']['eosnode-1']['bmc']['user'] }} passwd={{ salt['lyveutil.decrypt'](pillar['cluster']['eosnode-1']['bmc']['secret'], 'cluster') }} delay=5 pcmk_host_list={{ pillar['cluster']['eosnode-1']['hostname'] }} pcmk_host_check=static-list power_timeout=40 op monitor interval=10s
    - unless: pcs stonith show stonith-c1

Prepare for stonith on node-2:
  cmd.run:
    - name: pcs stonith create stonith-c2 fence_ipmilan ipaddr={{ pillar['cluster']['eosnode-2']['bmc']['ip'] }} login={{ pillar['cluster']['eosnode-2']['bmc']['user'] }} passwd={{ salt['lyveutil.decrypt'](pillar['cluster']['eosnode-2']['bmc']['secret'], 'cluster') }} pcmk_host_list={{ pillar['cluster']['eosnode-2']['hostname'] }} pcmk_host_check=static-list power_timeout=40 op monitor interval=10s
    - unless: pcs stonith show stonith-c2

Apply stonith for node-1:
  cmd.run:
    - name: pcs constraint location stonith-c1 avoids {{ pillar['cluster']['eosnode-1']['hostname'] }}=INFINITY

Apply stonith for node-2:
  cmd.run:
    - name: pcs constraint location stonith-c2 avoids {{ pillar['cluster']['eosnode-2']['hostname'] }}=INFINITY

{% endif %}
