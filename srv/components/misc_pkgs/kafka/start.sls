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

#Start zoopkeper:
#  cmd.run:
#    - name: ./bin/zookeeper-server-start.sh -daemon config/zookeeper.properties
#    - cwd: /opt/kafka
#    - unless: test 1 -le $(ps ax | grep java | grep -i QuorumPeerMain | grep -v grep | awk '{print $1}' | wc -l)

Start zoopkeper:
  service.running:
    - name: kafka-zookeeper
    - enable: True

#TODO: find better solution to add delay
Wait for zookeeper to start:
  module.run:
    - test.sleep:
      - length: 10
    - require:
      - Start zoopkeper

#Start kafka:
#  cmd.run:
#    - name: ./bin/kafka-server-start.sh -daemon config/server.properties
#    - cwd: /opt/kafka
#    - unless: test 1 -le $(ps ax | grep ' kafka\.Kafka ' | grep java | grep -v grep | awk '{print $1}' | wc -l)

Start kafka:
  service.running:
    - name: kafka
    - enable: True
    - require:
      - Wait for zookeeper to start
