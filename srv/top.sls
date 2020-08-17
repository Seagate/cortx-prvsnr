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

base:
  '*':
    - components.system
    - components.system.storage
    # Dependecies
    - components.misc_pkgs.build_ssl_cert_rpms
    - components.misc_pkgs.rsyslog
    - components.ha.corosync-pacemaker
    - components.ha.haproxy
    - components.misc_pkgs.elasticsearch
    - components.misc_pkgs.kibana
    - components.misc_pkgs.nodejs
    - components.misc_pkgs.openldap
    - components.misc_pkgs.rabbitmq
    - components.misc_pkgs.statsd
    - components.misc_pkgs.ssl_certs
    # IO Stack
    - components.misc_pkgs.lustre
    - components.motr
    - components.s3server
    - components.hare
    # Management Stack
    - components.sspl
    - components.csm
