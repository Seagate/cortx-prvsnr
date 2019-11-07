base:
  'G@roles:primary':
    - roles.primary
  '*':
    - components.cluster
    - components.corosync-pacemaker
    - components.halon
    - components.haproxy
    - components.eoscore
    - components.openldap
    - components.rabbitmq
    - components.release
    - components.s3client
    - components.s3server
    - components.sspl
    - components.system
