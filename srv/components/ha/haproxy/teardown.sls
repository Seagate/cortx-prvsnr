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

Disable rsyslog:
  service.dead:
    - name: rsyslog
    - enable: False

Remove haproxy config:
  file.absent:
    - name: /etc/haproxy

Remove haproxy 503 error code to http file:
  file.absent:
    - name: /etc/haproxy/errors/503.http

Remove haproxy config to enable logs:
  file.absent:
    - name: /etc/rsyslog.d/haproxy.conf

Remove logrotate config for haproxy to run hourly:
  file.absent:
    - name: /etc/cron.hourly/logrotate

Clean existing logrotate configuration to run daily:
  file.absent:
    - name: /etc/cron.daily/logrotate

Remove logrotate config for haproxy:
  file.absent:
    - name: /etc/logrotate.d/haproxy

Remove haproxy:
  pkg.purged:
    - name: haproxy

Remove user haproxy:
  user.absent:
    - name: haproxy
    - purge: True
    - force: True

Reset selinux bool for haproxy:
  selinux.boolean:
    - name: haproxy_connect_any
    - value: 0
    - persist: True

Reset selinux bool for httpd:
  selinux.boolean:
    - name: httpd_can_network_connect
    - value: false
    - persist: True

Remove haproxy user to certs group:
  group.present:
    - name: certs
    - delusers:
      - haproxy
