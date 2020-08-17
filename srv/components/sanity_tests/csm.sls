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

{% if pillar['cluster'][grains['id']]['is_primary'] -%}

{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}

Run CSM sanity tests:
  cmd.run:
    - name: /usr/bin/csm_test -f /opt/seagate/cortx/csm/test/test_data/args.yaml -t /opt/seagate/cortx/csm/test/plans/self_test.pln 2>&1 | tee -a {{ logfile }}

{% endif %}
