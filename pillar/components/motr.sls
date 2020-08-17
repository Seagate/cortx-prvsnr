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

motr:
    # Minimum rpc receive queue length
    MOTR_M0D_MIN_RPC_RECVQ_LEN: 512
    # ioservice buffer pool configuration
    MOTR_M0D_IOS_BUFFER_POOL_SIZE: 512
    # BE related
    MOTR_M0D_BETXGR_TX_NR_MAX: 82
    MOTR_M0D_BETXGR_REG_NR_MAX: 2097152
    MOTR_M0D_BETXGR_REG_SIZE_MAX: 536870912
    MOTR_M0D_BETXGR_PAYLOAD_SIZE_MAX: 134217728
    MOTR_M0D_BETXGR_FREEZE_TIMEOUT_MIN: 300
    MOTR_M0D_BETXGR_FREEZE_TIMEOUT_MAX: 300
    MOTR_M0D_BETX_REG_NR_MAX: 262144
    MOTR_M0D_BETX_REG_SIZE_MAX: 41943040
    MOTR_M0D_BETX_PAYLOAD_SIZE_MAX: 2097152
    # Can be set to a number of seconds for m0traced to monitor input file creation
    MOTR_TRACED_CHECK_INPUT: 30
    # How many log pieces to keep in rotation, lower margin (-k option of m0traced)
    MOTR_TRACED_MIN_LOG_CHUNKS: 2
    # How many log pieces to keep in rotation, upper margin (-k option of m0traced)
    MOTR_TRACED_MAX_LOG_CHUNKS: 6
    # Minimal size of individual log chunk in rotation set (-s option of m0traced)
    MOTR_TRACED_MIN_LOG_CHUNK_SIZE_MB: 16
    # Maximal size of individual log chunk in rotation set (-s option of m0traced)
    MOTR_TRACED_MAX_LOG_CHUNK_SIZE_MB: 1024
    # How many log sets to keep for each service (between restarts)
    MOTR_TRACED_KEEP_LOGS_NUM: 2
    MOTR_M0D_BESEG_SIZE: 4294967296
