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

sspl:
  health_map_path: /opt/seagate/cortx_configs/healthmap/
  health_map_file: healthmap-schema.json
  rmq:
    user: rmq
    secret:
  role: cortx
  Version: 1.0.0
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
  NODEDATA:
    probe:sysfs
  SASPORTSENSOR:
    threaded: "true"
    probe: sysfs
    polling_frequency: "30"
  MEMFAULTSENSOR:
    threaded: "true"
    probe: procfs
  CPUFAULTSENSOR:
    threaded: "true"
    probe: sysfs
  LOGGINGPROCESSOR:
    virtual_host: "SSPL"
    queue_name: "iem-queue"
    exchange_name: "sspl-in"
    routing_key: "iem-key"
    username: "sspluser"
    password:
    primary_rabbitmq_host: "localhost"
  LOGGINGMSGHANDLER:
    iem_routing_enabled: "false"
    iem_log_locally: "true"
  DISKMSGHANDLER:
    dmreport_file: "/tmp/sspl/drivemanager/drive_manager.json"
    always_log_iem: "False"
    max_drivemanager_events: "14"
    max_drivemanager_event_interval: "10"
  NODEDATAMSGHANDLER:
    transmit_interval: "10"
    units: "MB"
    disk_usage_threshold: "80"
    cpu_usage_threshold: "80"
    host_memory_usage_threshold: "80"
  RARITANPDU:
    user: "admin"
    pass: "admin"
    comm_port: "/dev/ttyACM0"
    IP_addr: "172.16.1.222"
    max_login_attempts: "2"
  RAIDSENSOR:
    threaded: "true"
    RAID_status_file: "/proc/mdstat"
  RAIDINTEGRITYSENSOR:
    threaded: "true"
    polling_interval: "1209600"
  IPMI:
    user: "admin"
    pass: "admin"
  SMTPSETTING:
    smptserver: "mailhost.seagate.com"
    recipient: "example@seagate.com"
    smtp_port: "25"
  LOGEMAILER:
    priority: "LOG_ERR"
  SMRDRIVEDATA:
    threaded: "true"
    logging_interval: "3600"
  STORAGE_ENCLOSURE:
    primary_controller_ip: "127.0.0.1"
    primary_controller_port: "28200"
    secondary_controller_ip: "127.0.0.1"
    secondary_controller_port: "28200"
    user: "xxxxx"
    password:
    mgmt_interface: "cliapi"
  REALSTORSENSORS:
    polling_frequency: "30"
  REALSTORPSUSENSOR:
    threaded: "true"
  REALSTORFANSENSOR:
    threaded: "true"
  REALSTORCONTROLLERSENSOR:
    threaded: "true"
  REALSTORDISKSENSOR:
    threaded: "true"
    polling_frequency_override: "0"
  REALSTORSIDEPLANEEXPANDERSENSOR:
    threaded: "true"
  NODEHWSENSOR:
    threaded: "true"
    polling_interval: "30"
  REALSTORLOGICALVOLUMESENSOR:
    threaded: "true"
  REALSTORENCLOSURESENSOR:
    threaded: "true"
  IEMSENSOR:
    threaded: "true"
    log_file_path: "/var/log/cortx/iem/iem_messages"
    timestamp_file_path: "/var/cortx/sspl/data/iem/last_processed_msg_time"
  SYSTEMDWATCHDOG:
    threaded: "true"
    smart_test_interval: "999999999"
    run_smart_on_start: "False"
  NODEHWACTUATOR:
    ipmi_client: "ipmitool"
  DATASTORE:
    store_type: "consul"
    consul_host: "127.0.0.1"
    consul_port: "8500"
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
    ack_queue_name: "sensor-queue"
    ack_exchange_name: "sspl-out"
    ack_routing_key: "sensor-key"
    username: "sspluser"
    password:
    message_signature_username: "sspl-ll"
    message_signature_token: "ALOIUD986798df69a8koDISLKJ282983"
    message_signature_expires: "3600"
    iem_route_exchange_name: "sspl-out"
    primary_rabbitmq_host: "localhost"
