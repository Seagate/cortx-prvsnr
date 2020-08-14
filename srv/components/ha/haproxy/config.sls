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
