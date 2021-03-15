firewall:
  data_public:
    services:
      - ssh
      - high-availability
    ports:
      consul:
        - 8600/tcp
        - 8600/udp
        - 8500/tcp
        - 8301/tcp
        - 8301/udp
        - 8302/tcp
        - 8302/udp
        - 8300/tcp
      dhclient:
        - 68/udp
      dhserver:
        - 67/udp
      hare:
        - 8008/tcp
      nfs:
        - 2049/tcp
        - 2049/udp
        - 32803/tcp
        - 892/tcp
        - 875/tcp
      uds:
        - 5000/tcp
        - 5125/udp
      www:
        - 443/tcp
      s3:
        - 7081/tcp
        {% for port in range(8081, 8099) %}
        - {{ port }}/tcp
        {% endfor %}
        - 514/tcp
        - 514/udp
        - 8125/tcp
        - 6379/tcp
        - 9443/tcp
        - 9086/tcp
  mgmt_public:
    services:
      - ssh
      - high-availability
      - ftp
      {%- if salt['cmd.run']('rpm -qa glusterfs-server') %}
      - glusterfs
      {%- endif %}
    ports:
      consul:
        - 8600/tcp
        - 8600/udp
        - 8500/tcp
        - 8301/tcp
        - 8301/udp
        - 8302/tcp
        - 8302/udp
        - 8300/tcp
      csm:
        - 28100/tcp
        - 28101/tcp
        - 28102/tcp
        - 28103/tcp
      dhclient:
        - 68/udp
      elasticsearch:
        - 9200/tcp
        - 9300/tcp
      ntpd:
        - 123/udp
      openldap:
        - 389/tcp
      smtp:
        - 25/tcp
      saltmaster:
        - 4505/tcp
        - 4506/tcp
      uds:
        - 5000/tcp
        - 5125/udp
      www:
        - 443/tcp
