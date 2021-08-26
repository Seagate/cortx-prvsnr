firewall:
  data_private:
    ports:
      consul:
        - 8300/tcp
        - 8301/tcp
        - 8301/udp
        - 8302/tcp
        - 8302/udp
        - 8500/tcp            
      csm_agent:
        - 28101/tcp
      dhclient:
        - 68/udp
      haproxy_dummy:
        - 28001/tcp
        - 28002/tcp
      hax:
        - 8008/tcp
      kafka:
        - 9092/tcp
      lnet:
        - 988/tcp
      rest_server:
        - 28300/tcp
      rsyslog:
        - 514/tcp
      s3authserver:
        - 28050/tcp
      s3server:
        - 28071/tcp
        - 28072/tcp
        - 28073/tcp
        - 28074/tcp
        - 28075/tcp
        - 28076/tcp
        - 28077/tcp
        - 28078/tcp
        - 28079/tcp
        - 28080/tcp
        - 28081/tcp
        - 28082/tcp
        - 28083/tcp
        - 28084/tcp
        - 28085/tcp
        - 28086/tcp
        - 28087/tcp
        - 28088/tcp
        - 28089/tcp
        - 28090/tcp
        - 28091/tcp
        - 29092/tcp
        - 28049/tcp
      statsd:
        - 5601/tcp
        - 8125/tcp
      zookeeper:
        - 2181/tcp
        - 2888/tcp
        - 3888/tcp
    services:
      - elasticsearch
      - high-availability
      - ldap
      - ldaps
      - ssh
  data_public:
    ports:
      haproxy:
        - 443/tcp
      s3:
        - 9080/tcp
        - 9443/tcp
    services:
      - http
      - https
      - ssh
  mgmt_public:
    ports:
      csm:
        - 28100/tcp
    services:
      - http
      - https
      - ftp
      - ntp
      - salt-master
      - ssh
      - glusterfs
