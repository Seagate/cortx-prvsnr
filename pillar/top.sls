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
    - components.haproxy
    - components.openldap
    - components.release
    - components.s3client
    - components.system
    - user.*
    - ignore_missing: True
