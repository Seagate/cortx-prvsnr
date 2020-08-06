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

#!/bin/bash

set -eux

# openssh-clients is necessary for scp on server side as well
yum -y install openssh-server openssh-clients

sed -i "s/#UsePrivilegeSeparation.*/UsePrivilegeSeparation no/g" /etc/ssh/sshd_config
sed -i 's/^#\?AuthorizedKeysFile.*/AuthorizedKeysFile .ssh\/authorized_keys .ssh\/authorized_keys_test/g' /etc/ssh/sshd_config

systemctl enable sshd.service

mkdir -p /root/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDqJFVMGBchNGDA5ie2CDFT9rTuZMQrG/xTlmD5xR9o38xBYgGAlBuUMofMD9h+hiUpBIFehVRyQc9GmFXzilwCG3IOmahgIk8kuYCajwXSZBfE1uTFxhQBYc2wYA5nD/wr5j6do091DHCEcFKVevpxw5qW58p9CDC/SYq/ztMqr+fxvqH8walNQhfpALNdIKqh/CZJbo+lJ0MVAuCACjJRNVO5iQuz85pQ40WmDmJrVXJvtNCN/dZY3dN0l4Wo/K6wkhwBiyvIyVsSM4UPavxIetCg85u6vvcPBseQJSo/il9ustyeahY05V3p1FFfFRD9iRNFTyoXpAABK0bzZWDGY/kGV1uZvotfNwpavNzdbSsbeHcvNhsXfH0ZZG2dOKUGuyDrKMr9uDJP3hosRz+f9tLx19LYWGXPzzf3aGGpV9hZtIGNWKfIKLfp18O3nhfa1BVlMDh9bxb6lishzGQxP72Aw4NMaYX3GF3XYLZY5SA8n24nofOtIv9+Qx1W7X7XvoQK/L+UkC0/ZAQvLrnHu0g8crcTp5VyKpIHDzlnurqtPGvznMAXkkm985p6HMIWF7Gb6w7PNfl6gwHa/ve2fbKzDoByqHydu0Dij525Tgh61EokLRadWhX5I7SngC0u9HeuCpRcCR3KDP/bF2msV2o/FvrV1ncBpqxr8pWfJQ== test@seagate.com" > /root/.ssh/authorized_keys_test

rm -rf /var/cache/yum
