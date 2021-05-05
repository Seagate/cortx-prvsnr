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

#Stop kafka:
#  cmd.run:
#    - name: ./bin/kafka-server-stop.sh -daemon config/server.properties
#    - cwd: /opt/kafka
#    - onlyif: test 1 -le $(ps ax | grep ' kafka\.Kafka ' | grep java | grep -v grep | awk '{print $1}' | wc -l)

Stop kafka:
  service.dead:
    - name: kafka

Ensure kafka has stopped:
  cmd.run:
    - name: test 1 -le $(ps ax | grep -i 'kafka.Kafka' | grep -v grep | awk '{print $1}' | wc -l)
    - retry:
    # Ref: https://docs.saltproject.io/en/3000/ref/states/requisites.html#retrying-states
        attempts: 10
        until: False
        interval: 2
    - require:
      - Start kafka

#Stop zookeeper:
#  cmd.run:
#    - name: ./bin/zookeeper-server-stop.sh -daemon config/zookeeper.properties
#    - cwd: /opt/kafka
#    - onlyif: test 1 -le $(ps ax | grep java | grep -i QuorumPeerMain | grep -v grep | awk '{print $1}' | wc -l)
#    - require:
#      - Ensure kafka has stopped

Stop zookeeper:
  service.dead:
    - name: kafka-zookeeper
    - require:
      - Ensure kafka has stopped

Ensure kafka-zookeeper has stopped:
  cmd.run:
    - name: test 1 -le $(ps ax | grep java | grep -i QuorumPeerMain | grep -v grep | awk '{print $1}' | wc -l)
    - retry:
    # Ref: https://docs.saltproject.io/en/3000/ref/states/requisites.html#retrying-states
        attempts: 10
        until: False
        interval: 2
    - require:
      - Stop zookeeper
