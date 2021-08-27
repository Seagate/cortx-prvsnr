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
        {%- for port in range(28071,28093) %}
        - {{ port }}/tcp
        {% endfor -%}
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
