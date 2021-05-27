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

Ensure kafka-zookeeper has started:
  cmd.run:
    - name: test 1 -le $(ps ax | grep java | grep -i QuorumPeerMain | grep -v grep | awk '{print $1}' | wc -l)
    - retry:
    # Ref: https://docs.saltproject.io/en/3002/ref/states/requisites.html#retrying-states
        # Until condition here is quite tricky, esp. in case of cmd.run.
        # If you wonder why this case doesn't result in infinite loop before timing out, read further.
        # Command test 0 -eq ${var} results in non-zero code for inequality.
        # Non-zero value is True for Python. So in "Until", check results true; although shell interprets as false.
        # The reverse happens when shell we have a true condition with ret-code '0'. until results in false.
        # Note this when interpreting the next line.
        until: True
        attempts: 10
        interval: 2
    - require:
      - Start zoopkeper

# Start kafka:
#  cmd.run:
#    - name: ./bin/kafka-server-start.sh -daemon config/server.properties
#    - cwd: /opt/kafka
#    - unless: test 1 -le $(ps ax | grep ' kafka\.Kafka ' | grep java | grep -v grep | awk '{print $1}' | wc -l)
#    - require:
#       - Ensure kafka-zookeeper has started

Start kafka:
  service.running:
    - name: kafka
    - enable: True
    - require:
      - Ensure kafka-zookeeper has started

Ensure kafka has started:
  cmd.run:
    - name: test 1 -le $(ps ax | grep ' kafka\.Kafka ' | grep java | grep -v grep | awk '{print $1}' | wc -l)
    - retry:
    # Ref: https://docs.saltproject.io/en/3002/ref/states/requisites.html#retrying-states
        # Until condition here is quite tricky, esp. in case of cmd.run.
        # If you wonder why this case doesn't result in infinite loop before timing out, read further.
        # Command test 0 -eq ${var} results in non-zero code for inequality.
        # Non-zero value is True for Python. So in "Until", check results true; although shell interprets as false.
        # The reverse happens when shell we have a true condition with ret-code '0'. until results in false.
        # Note this when interpreting the next line.
        until: True
        attempts: 10
        interval: 2
    - require:
      - Start kafka
