base:
  'G@roles:primary':
    - roles.primary
  '*':
    # - node_info.node_data
    - components.cluster
    - components.corosync-pacemaker
    - components.halon
    - components.haproxy
    - components.eoscore
    - components.openldap
    - components.rabbitmq
    - components.release
    - components.s3client
    - components.sspl
    - components.system
    - components.elasticsearch
    - components.elasticsearch
    - user.*
    - ignore_missing: True
