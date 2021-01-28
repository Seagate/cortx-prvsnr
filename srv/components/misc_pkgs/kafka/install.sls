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

{% import_yaml 'components/defaults.yaml' as defaults %}

{% set kafka_version = pillar['commons']['version']['kafka'] %}

Install Java:
  pkg.installed:
    - pkgs:
      - java-1.8.0-openjdk-headless
      #- java-1.8.0-openjdk-devel

Extract Kafka:
  archive.extracted:
    - name: /opt/kafka
    - source: {{ defaults.commons.repo.url }}/commons/kafka/kafka_{{ kafka_version }}.tgz
    - keep_source: True
    - clean: True
    - trim_output: True
    - skip_verify: True

Install kafka client python package:
  pip.installed:
    - name: confluent-kafka
    - bin_env: /usr/bin/pip3
    - target: /usr/lib64/python3.6/site-packages/
