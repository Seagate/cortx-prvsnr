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

{% set kafka_version = pillar['commons']['version']['kafka'] %}

Stop zookeeper:
  cmd.run:
    - name: ./bin/zookeeper-server-stop.sh -daemon config/zookeeper.properties
    - cwd: /opt/kafka/kafka_{{ kafka_version }}
    - onlyif: ps ax | grep 'zookeeper' | grep -v grep

Stop kafka:
  cmd.run:
    - name: ./bin/kafka-server-stop.sh -daemon config/server.properties
    - cwd: /opt/kafka/kafka_{{ kafka_version }}
    - onlyif: ps ax | grep 'kafka' | grep -v grep

{% set zookeeper_pid = salt['cmd.shell']("ps ax | grep zookeeper | grep -v grep | awk '{{print $1}}'") %}
Kill zookeeper process:
  module.run:
    - ps.kill_pid:
      - pid: {{ zookeeper_pid }}
      - signal: 9

{% set kafka_pid = salt['cmd.shell']("ps ax | grep kafka | grep -v grep | awk '{{print $1}}'") %}
Kill kafka process:
  module.run:
    - ps.kill_pid:
      - pid: {{ kafka_pid }}
      - signal: 9

Remove java:
  pkg.purged:
    - name: java-1.8.0-openjdk-headless

Remove kafka directory:
  file.absent:
    - name: /opt/kafka/kafka_{{ kafka_version }}

Remove zookeeper data directory:
  file.absent:
    - name: /var/lib/zookeeper

Remove kafka flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.kafka
