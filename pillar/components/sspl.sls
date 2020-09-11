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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

sspl:
  SYSTEM_INFORMATION:
    operating_system: "centos7"
    product: "ECS"
    cli_type: "CS-A"
    setup: "cortx"
    data_path: "/var/cortx/sspl/data/"
    cluster_id: "001"
    site_id: "001"
    rack_id: "001"
    node_id: "001"
    log_level: "INFO"
    sspl_log_file_path: "/var/log/cortx/sspl/sspl.log"
    syslog_host: "localhost"
    syslog_port: "514"
  LOGGINGPROCESSOR:
    virtual_host: "SSPL"
    queue_name: "iem-queue"
    exchange_name: "sspl-in"
    routing_key: "iem-key"
    username: "sspluser"
    password: "sspl4ever"
    primary_rabbitmq_host: "localhost"
  STORAGE_ENCLOSURE:
    primary_controller_ip: "127.0.0.1"
    primary_controller_port: "28200"
    secondary_controller_ip: "127.0.0.1"
    secondary_controller_port: "28200"
    user: "xxxxx"
    password: "gAAAAABehkmVHStx337AN2g6OTALqA5BNejmWD6Nu__25DgYzauLz6iGLLCDzqs71pP7Z5AV-oEvnOPGKomJiTzyPwOHnmylEQ=="
    mgmt_interface: "cliapi"
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
    ack_queue_name: "sensor-queue"
    ack_exchange_name: "sspl-out"
    ack_routing_key: "sensor-key"
    username: "sspluser"
    password: "sspl4ever"
    message_signature_username: "sspl-ll"
    message_signature_token: "ALOIUD986798df69a8koDISLKJ282983"
    message_signature_expires: "3600"
    iem_route_exchange_name: "sspl-out"
    primary_rabbitmq_host: "localhost"
