s3server:
  reuseport: false
  ipv4_bind_addr: 0.0.0.0
  ipv6_bind_addr: ~
  bind_port: 8081
  default_endpoint: s3.seagate.com
  region_endpoints: [s3-us-west-2.seagate.com, s3-us.seagate.com, s3-europe.seagate.com, s3-asia.seagate.com]
  read_ahead_multiple: 2
ssl:
  enable: false
performance_local_stats:
  enable: 0
logging:
  mode: DEBUG   # DEBUG, INFO, WARN, ERROR, FATAL,
  enable_buffering: false
auth_server:
  ssl: true
  ip_addr: ipv4:127.0.0.1        # Auth server IP address Should be in below format:
                                 # ipv4 address format: ipv4:127.0.0.1
                                 # ipv6 address format: ipv6:::1
  port: 9086                     # Auth server port for https request
statsd:
  enable: false        # Enable the Stats feature. Default is false.
  ip_addr: 127.0.0.1   # StatsD server IP address
  port: 8125           # StatsD server port
  whitelisting: "/opt/seagate/s3/conf/s3stats-whitelist.yaml"  # White list of Stats metrics to be published to the backend.
clovis:  # Section for S3 Clovis
  max_units_per_request: 8    # Maximum units per read/write request to clovis
  max_idx_kv_fetch_count: 30  # COSTOR-157. Clovis will read from index(If not specified) at a time maximim of this many key values
  tm_recv_queue_min_len: 16   # Minimum length of the 'tm' receive queue for clovis, default is 2
  max_rpc_msg_size: 262144    # COSTOR-157. Maximum rpc message size for clovis, default is 131072 (128k)
  memory_pool:
    unit_sizes: [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304]                          # Memory pool will be created for each of this unit_size with following properties
    read_initial_buffer_count: 10        # 10 blocks, the initial pool size = multiple of S3_CLOVIS_UNIT_SIZE
    read_expandable_count: 50            # 50 blocks, pool's expandable size, multiple of S3_CLOVIS_UNIT_SIZE
    read_max_threshold_in_bytes: 524288000        # 500 MB, The maximum memory threshold for the pool, multiple of S3_CLOVIS_UNIT_SIZE
thirdparty:
  libevent:
    max_read_size_in_bytes: 16384           # Maximum read in a single read operation, as per libevent documentation in code, user should not try to read more than this value
    memory_pool:
      pool_buffer_size_in_bytes: 16384      # Pool buffer size, in case of S3_CLOVIS_UNIT_SIZE of size 1MB, it is recommended to have S3_LIBEVENT_POOL_BUFFER_SIZE of size 16384
      initial_size_in_bytes: 104857600      # Hundred 1mb blocks, the initial pool size, multiple of S3_CLOVIS_UNIT_SIZE
      expandable_size_in_bytes: 104857600   # 100mb, pool's expandable size, multiple of S3_CLOVIS_UNIT_SIZE
      max_threshold_in_bytes: 524288000     # 500 MB, The maximum memory threshold for the pool, multiple of S3_CLOVIS_UNIT_SIZE
