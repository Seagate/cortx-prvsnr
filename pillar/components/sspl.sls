sspl:
  role: eos
  # Version 1.0.0

  SSPL-LL_SETTING:
    core_processors: [RabbitMQegressProcessor, RabbitMQingressProcessor, LoggingProcessor]
    message_handlers: [DiskMsgHandler, LoggingMsgHandler, ServiceMsgHandler, NodeDataMsgHandler, NodeControllerMsgHandler, RealStorEnclMsgHandler]
    sensors: [ServiceWatchdog, NodeData, RAIDsensor, RealStorFanSensor, RealStorPSUSensor, RealStorControllerSensor, RealStorDiskSensor, RealStorSideplaneExpanderSensor]
    actuators: [Service, RAIDactuator, Hdparm]

  SYSTEM_INFORMATION:
    operating_system: centos7
    product: EES
    cli_type: CS-A
    setup: eos
    data_path: /var/sspl/data/

  RABBITMQINGRESSPROCESSOR:
    virtual_host: SSPL
    queue_name: actuator-req-queue
    exchange_name: sspl-in
    routing_key: actuator-req-key
    username: sspluser
    password: sspl4ever
    primary_rabbitmq_host: localhost

  RABBITMQEGRESSPROCESSOR:
    virtual_host: SSPL
    queue_name: sensor-queue
    exchange_name: sspl-out
    routing_key: sensor-key
    ack_queue_name: actuator-resp-queue
    ack_exchange_name: sspl-out
    ack_routing_key: actuator-resp-key
    username: sspluser
    password: sspl4ever
    message_signature_username: sspl-ll
    message_signature_token: ALOIUD986798df69a8koDISLKJ282983
    message_signature_expires: 3600
    iem_route_addr: 
    iem_route_exchange_name: sspl-out
    primary_rabbitmq_host: localhost

  LOGGINGPROCESSOR:
    virtual_host: SSPL
    queue_name: iem-queue
    exchange_name: sspl-in
    routing_key: iem-key
    username: sspluser
    password: sspl4ever
    primary_rabbitmq_host: localhost

  LOGGINGMSGHANDLER:
    iem_routing_enabled: false
    iem_log_locally: true

  DISKMSGHANDLER:
    dmreport_file: /tmp/sspl/drivemanager/drive_manager.json
    always_log_iem: False
    max_drivemanager_events: 14
    max_drivemanager_event_interval: 10

  NODEDATAMSGHANDLER:
    transmit_interval: 300
    units: MB

  XINITDWATCHDOG:
    threaded: true
    monitored_services: 

  RARITANPDU:
    user: admin
    pass: admin
    comm_port: /dev/ttyACM0
    IP_addr: 172.16.1.222
    max_login_attempts: 2

  RAIDSENSOR:
    threaded: true
    RAID_status_file: /proc/mdstat

  IPMI:
    user: admin
    pass: admin

  SMTPSETTING:
    smptserver: mailhost.seagate.com
    recipient: malhar.vora@seagate.com
    smtp_port: 25
    username: 
    password: 

  LOGEMAILER:
    priority: LOG_ERR

  SMRDRIVEDATA:
    threaded: true
    logging_interval: 3600

  STORAGE_ENCLOSURE:
    primary_controller_ip: 127.0.0.1
    primary_controller_port: 80
    secondary_controller_ip: 127.0.0.1
    secondary_controller_port: 80
    user: xxxxx
    password: xxxxx

  REALSTORPSUSENSOR:
    threaded: true

  REALSTORFANSENSOR:
    threaded: true

  REALSTORCONTROLLERSENSOR:
    threaded: true

  REALSTORDISKSENSOR:
    threaded: true
    polling_frequency_override: 0

  REALSTORSIDEPLANEEXPANDERSENSOR:
    threaded: true