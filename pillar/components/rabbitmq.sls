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
