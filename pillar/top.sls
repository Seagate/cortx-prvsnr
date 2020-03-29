base:
  'G@roles:primary':
    - roles.primary
  '*':
    - ignore_missing: True
    # - node_info.node_data
    - components.cluster                    # default all minions vars (here and below) TODO create task: move to groups.all.components...
    - components.commons
    - components.corosync-pacemaker
    - components.elasticsearch
    - components.eoscore
    - components.haproxy
    - components.openldap
    - components.release
    - components.s3clients
    - components.s3server
    - components.system
    - components.sspl
    - components.uds
    - user.groups.all.*                     # user all minions vars
  {{ grains.id }}:
    - ignore_missing: True
    - minions.{{ grains.id }}.*             # default per-minion vars
    - user.minions.{{ grains.id }}.*   # user per-minion vars
