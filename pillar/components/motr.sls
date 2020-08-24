#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
