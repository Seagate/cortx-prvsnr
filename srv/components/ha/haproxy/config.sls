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

Add haproxy user to certs group:
  group.present:
    - name: certs
    - addusers:
      - haproxy

Setup HAProxy config:
  file.managed:
    - name: /etc/haproxy/haproxy.cfg
    - source: salt://components/ha/haproxy/files/haproxy.cfg
    - makedirs: True
    - keep_source: False
    - template: jinja

Setup haproxy 503 error code to http file:
  file.managed:
    - name: /etc/haproxy/errors/503.http
    - source: salt://components/ha/haproxy/files/503.http
    - makedirs: True
    - keep_source: False

Setup logrotate config for haproxy:
  file.managed:
    - name: /etc/logrotate.d/haproxy
    - source: salt://components/ha/haproxy/files/logrotate/haproxy
    - makedirs: True
    - keep_source: False

Setup logrotate cron for haproxy to run hourly:
  file.managed:
    - name: /etc/cron.hourly/logrotate
    - source: salt://components/ha/haproxy/files/logrotate/logrotate
    - keep_source: False
    - makedirs: True
    - mode: '0744'

Setup haproxy config to enable logs:
  file.managed:
    - name: /etc/rsyslog.d/haproxy.conf
    - source: salt://components/ha/haproxy/files/rsyslog.d/haproxy.conf
    - makedirs: True
    - keep_source: False

include:
  - components.misc_pkgs.rsyslog.start
