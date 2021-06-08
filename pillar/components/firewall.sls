firewall:
  data_public:
    services: []
    ports:
      haproxy:
        - 443/tcp
      s3:
        - 9443/tcp
{% if "physical" not in grains['virtual'] %}
      # Applicable only in VM environment, esp. OVA
      www:
        - 80/tcp
{% endif %}
  mgmt_public:
    services:
      - ssh
      - ftp
      {%- if salt['cmd.run']('rpm -qa glusterfs-server') %}
      - glusterfs
      {%- endif %}
    ports:
      csm:
        - 28100/tcp
      dhclient:
        - 68/udp
      dns:
        - 53/tcp
        - 53/udp
      ntpd:
        - 123/tcp
        - 123/udp
      redis:
        - 6379/tcp
        - 6379/udp
      smtp:
        - 25/tcp
      saltmaster:
        - 4505/tcp
        - 4506/tcp
      uds:
        - 5000/tcp
        - 5000/udp
{% if "physical" not in grains['virtual'] %}
      # Applicable only in VM environment, esp. OVA
      www:
        - 80/tcp
      haproxy:
        - 443/tcp
{% endif %}
