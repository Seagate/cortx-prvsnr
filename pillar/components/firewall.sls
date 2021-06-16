#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

# Check for default services udner:
# /usr/lib/firewalld/services/
firewall:
  # data_private:
  #   services:
  #     # elasticsearch: 9200, 9300
  #     - elasticsearch
  #     # high-availability: 2224, 3121, 5403, 5404/udp, 5405-5412/udp, 9929, 9929/udp, 21064
  #     - high-availability
  #     # ldap: 389
  #     - ldap
  #     # ldaps: 636
  #     - ldaps
  #     - ssh
  #   ports:
  #     - consul:
  #       - 8300/tcp
  #       - 8301/tcp
  #       - 8301/udp
  #       - 8302/tcp
  #       - 8302/udp
  #       - 8500/tcp
  #     - csm_agent:
  #       - 28101/tcp
  #     - haproxy_dummy:
  #       - 28001/tcp
  #       - 28002/tcp
  #     - hax:
  #       - 8008/tcp
  #     - kafka:
  #       - 9092/tcp
  #     - lnet:
  #       - 988/tcp
  #     - s3server:
  #       {% for port in range(28071,28093) %}
  #       - {{ port }}/tcp
  #       {% endfor %}
  #       - 28049/tcp
  #     - s3authserver:
  #       - 28050/tcp
  #     - statsd:
  #       - 5601/tcp
  #       - 8125/tcp
  #     - rest_server:
  #       - 28300/tcp
  #     - rsyslog:
  #       - 514/tcp
  #     - zookeeper:
  #       - 2181/tcp
  #       - 2888/tcp
  #       - 3888/tcp
  data_public:
    services:
      - http
      - https
      - salt-master
    ports:
      s3:
        - 9080/tcp
        - 9443/tcp
      uds:
        - 5000/tcp
  mgmt_public:
    services:
      # - dns
      # - dhcp
      - http
      - https
      - ftp
      - ntp
      - salt-master
      - ssh
      {%- if salt['cmd.run']('rpm -qa glusterfs-server') %}
      - glusterfs
      {%- endif %}
    ports:
      csm:
        - 28100/tcp
      # dhclient:
      #   - 68/udp
      # chronyd:
      #   - 123/tcp
      #   - 123/udp
      # redis:
      #   - 6379/tcp
      #   - 6379/udp
      # smtp:
      #   - 25/tcp
      # saltmaster:
      #   - 4505/tcp
      #   - 4506/tcp
