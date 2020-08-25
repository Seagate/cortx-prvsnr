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

release:
    base:
        # TODO IMPROVE EOS-12076 EOS-12334
        #      the same base location as for update repos so they might
        #      be mounted by prouction setup logic as well
        # base_dir: /opt/seagate/cortx/updates
        # TODO IMPROVE EOS-12076 EOS-12334
        #      make the same as for for update repos so they might
        #      be mounted by prouction setup logic as well
        # TODO IMPROVE EOS-12076 shorten path, use some global config variable
        base_dir: /var/lib/seagate/cortx/provisioner/local/cortx_repos
        repos:
            eee: null
