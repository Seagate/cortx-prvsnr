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

rabbitmq:
  cluster_nodes: localhost
  erlang_cookie: QLDZYPYEYGHECTHYQXFJ
  sspl:
    RABBITMQINGRESSPROCESSOR:
      virtual_host: "SSPL"
      queue_name: "actuator-req-queue"
      exchange_name: "sspl-in"
      routing_key: "actuator-req-key"
      username: "sspluser"
      password:
      primary_rabbitmq_host: "localhost"
    RABBITMQEGRESSPROCESSOR:
      virtual_host: "SSPL"
      queue_name: "sensor-queue"
      exchange_name: "sspl-out"
      routing_key: "sensor-key"
      ack_queue_name: "actuator-resp-queue"
      ack_exchange_name: "sspl-out"
      ack_routing_key: "actuator-resp-key"
      username: "sspluser"
      password:
      message_signature_username: "sspl-ll"
      message_signature_token: "ALOIUD986798df69a8koDISLKJ282983"
      message_signature_expires: "3600"
      iem_route_exchange_name: "sspl-out"
      primary_rabbitmq_host: "localhost"
