sspl:
  rmq:
      user: rmq
      secret: rmq
  healthmappath: /tmp/resource_health_view.json
  role: eos
  Version: 1.0.0
  SSPL-LL_SETTING:
    core_processors: "RabbitMQegressProcessor, RabbitMQingressProcessor, LoggingProcessor"
    message_handlers: "DiskMsgHandler, LoggingMsgHandler, ServiceMsgHandler, NodeDataMsgHandler, NodeControllerMsgHandler, RealStorEnclMsgHandler, RealStorActuatorMsgHandler"
    sensors: "ServiceWatchdog, RAIDsensor, NodeData, RealStorFanSensor, RealStorPSUSensor, RealStorControllerSensor, RealStorDiskSensor, RealStorSideplaneExpanderSensor, RealStorLogicalVolumeSensor, IEMSensor, NodeHWsensor"
    actuators: "Service, RAIDactuator, Smartctl, NodeHWactuator, RealStorActuator"
    degraded_state_modules: "ServiceWatchdog, RAIDsensor, NodeData, IEMSensor, NodeHWsensor, DiskMsgHandler, LoggingMsgHandler, ServiceMsgHandler, NodeDataMsgHandler, NodeControllerMsgHandler"
  SYSTEM_INFORMATION:
    operating_system: "centos7"
    product: "EES"
    cli_type: "CS-A"
    setup: "eos"
    data_path: "/var/eos/sspl/data/"
    cluster_id: "001"
    site_id: "001"
    rack_id: "001"
    node_id: "001"
    log_level: "INFO"
    sspl_log_file_path: "/var/log/eos/sspl/sspl.log"
    syslog_host: "localhost"
    syslog_port: "514"
  RABBITMQINGRESSPROCESSOR:
    virtual_host: "SSPL"
    queue_name: "actuator-req-queue"
    exchange_name: "sspl-in"
    routing_key: "actuator-req-key"
    username: "sspluser"
    password: "gAAAAABebhpiEnRxeA3xKLEjAXAsgNENSpIYOsuQ0sHOoJmdYiCiHb5DEHdx_mwyNV7oL6Zb2J0oGQP_Bcuy9j_CwgEK6swXwQ=="
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
    password: "gAAAAABebhpiEnRxeA3xKLEjAXAsgNENSpIYOsuQ0sHOoJmdYiCiHb5DEHdx_mwyNV7oL6Zb2J0oGQP_Bcuy9j_CwgEK6swXwQ=="
    message_signature_username: "sspl-ll"
    message_signature_token: "ALOIUD986798df69a8koDISLKJ282983"
    message_signature_expires: "3600"
    iem_route_exchange_name: "sspl-out"
    primary_rabbitmq_host: "localhost"
  LOGGINGPROCESSOR:
    virtual_host: "SSPL"
    queue_name: "iem-queue"
    exchange_name: "sspl-in"
    routing_key: "iem-key"
    username: "sspluser"
    password: "gAAAAABebhpiEnRxeA3xKLEjAXAsgNENSpIYOsuQ0sHOoJmdYiCiHb5DEHdx_mwyNV7oL6Zb2J0oGQP_Bcuy9j_CwgEK6swXwQ=="
    primary_rabbitmq_host: "localhost"
  RABBITMQCLUSTER:
    cluster_nodes: "localhost"
    erlang_cookie: "QLDZYPYEYGHECTHYQXFJ"
  LOGGINGMSGHANDLER:
    iem_routing_enabled: "false"
    iem_log_locally: "true"
  DISKMSGHANDLER:
    dmreport_file: "/tmp/sspl/drivemanager/drive_manager.json"
    always_log_iem: "False"
    max_drivemanager_events: "14"
    max_drivemanager_event_interval: "10"
  NODEDATAMSGHANDLER:
    transmit_interval: "300"
    units: "MB"
    disk_usage_threshold: "80"
    cpu_usage_threshold: "80"
    host_memory_usage_threshold: "80"
  XINITDWATCHDOG:
    threaded: "true"
  RARITANPDU:
    user: "admin"
    pass: "admin"
    comm_port: "/dev/ttyACM0"
    IP_addr: "172.16.1.222"
    max_login_attempts: "2"
  RAIDSENSOR:
    threaded: "true"
    RAID_status_file: "/proc/mdstat"
  IPMI:
    user: "admin"
    pass: "admin"
  SMTPSETTING:
    smptserver: "mailhost.seagate.com"
    recipient: "malhar.vora@seagate.com"
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
    password: "gAAAAABebhrVg8SWJf9d5suLyYupSQ77BqQdOCfFshWHtmc4_xJLNstgmeIX6bO19vwNb7zYrJElMuvX5FxY75hvZUlrQtcB0w=="
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
  IEMSENSOR:
    threaded: "true"
    log_file_path: "/var/log/eos/iem/iem_messages"
    timestamp_file_path: "/var/eos/sspl/data/iem/last_processed_msg_time"
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
