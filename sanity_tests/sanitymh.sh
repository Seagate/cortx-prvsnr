#!/bin/bash
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


set -e

############################
# Motr & Halon test script #
############################

dd if=/dev/urandom of=/tmp/128M bs=1M count=128

hctl mero status --json > mero_status.json
Profile=$(jq -r '.csrProfile' mero_status.json)
Fid=$(jq -r '.csrHosts[0][1].crnProcesses[0][0].r_fid' mero_status.json)
IPADDR=$(jq '.csrPrincipalRM.s_endpoints' mero_status.json | awk -F "@" '{if(NR==2) print $1}'| cut -c 4-)
cat <<EOF > sanity_io.yaml
CrateConfig_Sections: [MOTR_CONFIG, WORKLOAD_SPEC]

MOTR_CONFIG:
   MOTR_LOCAL_ADDR: $IPADDR@tcp:12345:41:302
   MOTR_HA_ADDR: $IPADDR@tcp:12345:34:101
   LIBMOTR_PROF: <$Profile>  # Profile
   LAYOUT_ID: 1                     # Defines the UNIT_SIZE
   IS_OOSTORE: 1                    # Is oostore-mode?
   IS_READ_VERIFY: 0                # Enable read-verify?
   LIBMOTR_TM_RECV_QUEUE_MIN_LEN: 16 # Minimum length of the receive queue
   LIBMOTR_MAX_RPC_MSG_SIZE: 65536   # Maximum rpc message size
   LIBMOTR_PROCESS_FID: <$Fid>
   LIBMOTR_IDX_SERVICE_ID: 1

LOG_LEVEL: 4  # err(0), warn(1), info(2), trace(3), debug(4)

WORKLOAD_SPEC:               # Workload specification section
   WORKLOAD:                 # First Workload
      WORKLOAD_TYPE: 1       # Index(0), IO(1)
      WORKLOAD_SEED: tstamp  # SEED to the random number generator
      OPCODE: 3              # CREATE(0), DELETE(1), READ(2), WRITE(3)
      LIBMOTR_IOSIZE: 4k      # Total Size of IO to perform per object
      BLOCK_SIZE: 4k         # In N+K conf set to (N * UNIT_SIZE) for max perf
      BLOCKS_PER_OP: 1       # Number of blocks per LIBMOTR operation
      MAX_NR_OPS: 1          # Max concurrent operations per thread
      NR_OBJS: 1024           # Number of objects to create by each thread
      NR_THREADS: 1          # Number of threads to run in this workload
      RAND_IO: 1             # Random (1) or sequential (0) IO?
      MODE: 1                # Synchronous=0, Asynchronous=1
      THREAD_OPS: 0          # All threads write to the same object?
      NR_ROUNDS: 1           # Number of times this workload is run
      EXEC_TIME: unlimited   # Execution time (secs or "unlimited")
      SOURCE_FILE: /tmp/128M # Source data file
EOF

m0crate -S ./sanity_io.yaml -U
rm -f ./sanity_io.yaml
rm -f /tmp/128M
