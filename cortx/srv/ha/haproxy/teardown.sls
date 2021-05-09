#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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

Remove haproxy service:
  file.absent:
    - name: /etc/systemd/system/haproxy.service.d/override.conf

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
