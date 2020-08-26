#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
      password: "sspl4ever"
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
      password: "sspl4ever"
      message_signature_username: "sspl-ll"
      message_signature_token: "ALOIUD986798df69a8koDISLKJ282983"
      message_signature_expires: "3600"
      iem_route_exchange_name: "sspl-out"
      primary_rabbitmq_host: "localhost"
