auth_server:
    ip_addr: ipv4:127.0.0.1
    port: 9086
    ssl: true
clovis:
    max_idx_kv_fetch_count: 30
    max_rpc_msg_size: 262144
    max_units_per_request: 8
    memory_pool:
        read_expandable_count: 50
        read_initial_buffer_count: 10
        read_max_threshold_in_bytes: 524288000
        unit_sizes:
        - 4096
        - 8192
        - 16384
        - 32768
        - 65536
        - 131072
        - 262144
        - 524288
        - 1048576
        - 2097152
        - 4194304
    tm_recv_queue_min_len: 16
logging:
    enable_buffering: false
    mode: DEBUG
performance_local_stats:
    enable: 0
s3server:
    bind_port: 8081
    default_endpoint: s3.seagate.com
    ipv4_bind_addr: 0.0.0.0
    ipv6_bind_addr: null
    read_ahead_multiple: 2
    region_endpoints:
    - s3-us-west-2.seagate.com
    - s3-us.seagate.com
    - s3-europe.seagate.com
    - s3-asia.seagate.com
    reuseport: false
ssl:
    enable: false
statsd:
    enable: false
    ip_addr: 127.0.0.1
    port: 8125
    whitelisting: /opt/seagate/s3/conf/s3stats-whitelist.yaml
thirdparty:
    libevent:
        max_read_size_in_bytes: 16384
        memory_pool:
            expandable_size_in_bytes: 104857600
            initial_size_in_bytes: 104857600
            max_threshold_in_bytes: 524288000
            pool_buffer_size_in_bytes: 16384
