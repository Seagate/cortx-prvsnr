base:
  'G@roles:primary':
    - roles.primary
  '*':
    # - node_info.node_data
    - components.cluster
    - components.commons
    - components.corosync-pacemaker
    - components.elasticsearch
    - components.eoscore
    - components.halon
    - components.haproxy
    - components.openldap
    - components.rabbitmq
    - components.release
    - components.s3client
    - components.s3server
    - components.sspl
    - components.system
    - user.*
    - ignore_missing: True
