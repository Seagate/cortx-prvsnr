eoscore:
    # Minimum rpc receive queue length
    MERO_M0D_MIN_RPC_RECVQ_LEN: 512
    # ioservice buffer pool configuration
    MERO_M0D_IOS_BUFFER_POOL_SIZE: 512
    # BE related
    MERO_M0D_BETXGR_TX_NR_MAX: 82
    MERO_M0D_BETXGR_REG_NR_MAX: 2097152
    MERO_M0D_BETXGR_REG_SIZE_MAX: 536870912
    MERO_M0D_BETXGR_PAYLOAD_SIZE_MAX: 134217728
    MERO_M0D_BETXGR_FREEZE_TIMEOUT_MIN: 300
    MERO_M0D_BETXGR_FREEZE_TIMEOUT_MAX: 300
    MERO_M0D_BETX_REG_NR_MAX: 262144
    MERO_M0D_BETX_REG_SIZE_MAX: 41943040
    MERO_M0D_BETX_PAYLOAD_SIZE_MAX: 2097152
    # Can be set to a number of seconds for m0traced to monitor input file creation
    MERO_TRACED_CHECK_INPUT: 30
    # How many log pieces to keep in rotation, lower margin (-k option of m0traced)
    MERO_TRACED_MIN_LOG_CHUNKS: 2
    # How many log pieces to keep in rotation, upper margin (-k option of m0traced)
    MERO_TRACED_MAX_LOG_CHUNKS: 6
    # Minimal size of individual log chunk in rotation set (-s option of m0traced)
    MERO_TRACED_MIN_LOG_CHUNK_SIZE_MB: 16
    # Maximal size of individual log chunk in rotation set (-s option of m0traced)
    MERO_TRACED_MAX_LOG_CHUNK_SIZE_MB: 1024
    # How many log sets to keep for each service (between restarts)
    MERO_TRACED_KEEP_LOGS_NUM: 2
    MERO_M0D_BESEG_SIZE: 4294967296
